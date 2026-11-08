(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.HyojaQueueCore = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";
  // 효자 병원 대기 v2 핵심 엔진 — 시험 전용. 실제 문자 발송·환자 정보·외부 연결 없음.
  var DEFAULTS = {
    MAX_AGE_MS: 120000, MAX_SKEW_MS: 30000, MAX_SEQ_GAP: 50, NEAR_AHEAD: 3,
    MAX_AHEAD: 500, MAX_ETA_MIN: 240, MAX_ATTEMPTS: 3, MAX_MSGS: 5,
    EXPIRE_MS: 6 * 3600000, SEEN_CAP: 1000, BACKOFF_MS: 60000,
    NEAR_MSG_TTL_MS: 600000, CALL_MSG_TTL_MS: 900000
  };
  var TYPES = ["waiting", "queue_changed", "paused", "resumed", "delayed", "called", "completed", "cancelled"];
  var TERMINAL = ["called", "completed", "cancelled", "expired"];
  var ID_RE = /^[A-Za-z0-9_\-:.]{1,64}$/;
  var LABEL_RE = /^[A-Za-z0-9\-]{1,10}$/;

  function qkey(h, q) { return h + "|" + q; }
  function tkey(h, q, t) { return h + "|" + q + "|" + t; }
  function isInt(n) { return typeof n === "number" && Number.isSafeInteger(n); }

  function createStore(opts) {
    return { cfg: Object.assign({}, DEFAULTS, opts || {}), queues: {}, tickets: {}, recipients: {} };
  }

  // 접수 등록: 동의·수신자 고정. 같은 접수 재등록은 기존 것을 돌려줌(중복 문자 방지).
  function register(store, r, now) {
    if (!r || ![r.hospitalId, r.queueId, r.ticketToken].every(function (x) { return typeof x === "string" && ID_RE.test(x); }))
      return { ok: false, reason: "invalid_ids" };
    if (typeof r.label !== "string" || !LABEL_RE.test(r.label)) return { ok: false, reason: "invalid_label" };
    var qk = qkey(r.hospitalId, r.queueId), tk = tkey(r.hospitalId, r.queueId, r.ticketToken);
    if (store.tickets[tk]) return { ok: true, duplicate: true, key: tk };
    var consent = r.consent === true;
    var ref = null;
    if (consent) {
      if (typeof r.recipientRef !== "string" || !ID_RE.test(r.recipientRef)) return { ok: false, reason: "invalid_recipient" };
      var rk = qk + "|" + r.recipientRef;
      if (store.recipients[rk]) return { ok: false, reason: "duplicate_recipient" };
      store.recipients[rk] = tk;
      ref = r.recipientRef;
    }
    if (!store.queues[qk]) {
      var base = isInt(r.baseSeq) && r.baseSeq >= 0 ? r.baseSeq : 0;
      store.queues[qk] = { lastSeq: base, seen: [], seenSet: {}, gapSeq: 0, blocked: false };
    }
    store.tickets[tk] = {
      key: tk, qk: qk, label: r.label, status: "waiting", ahead: null, estimate: null,
      observedAt: null, syncSeq: 0, lastEventAt: now, movedBack: false, consent: consent,
      recipientRef: ref, outbox: [], anomalies: []
    };
    return { ok: true, duplicate: false, key: tk };
  }

  function activeMsgs(t) { return t.outbox.filter(function (m) { return m.state !== "void"; }).length; }
  function enqueue(store, t, kind, text, now) {
    if (!t.consent) return null;
    var key = t.key + "|" + kind;
    if (t.outbox.some(function (m) { return m.key === key; })) return null;
    if (activeMsgs(t) >= store.cfg.MAX_MSGS) return null;
    var m = { key: key, kind: kind, text: text, state: "queued", attempts: 0, createdAt: now, nextAt: now, recipientRef: t.recipientRef };
    t.outbox.push(m);
    return m;
  }
  function voidPending(t, kinds) {
    t.outbox.forEach(function (m) {
      if ((m.state === "queued" || m.state === "failed") && (!kinds || kinds.indexOf(m.kind) >= 0)) m.state = "void";
    });
  }
  var TEXT = {
    near: function (l) { return "[효자] 접수번호 " + l + " 순서가 가까워졌어요. 화면과 병원 안내를 확인해 주세요. 병원 현장 호출이 우선입니다."; },
    called: function (l) { return "[효자] 접수번호 " + l + " 호출되었어요. 병원 안내에 따라 이동해 주세요."; },
    cancelled: function (l) { return "[효자] 접수번호 " + l + " 접수가 취소되었어요. 필요하면 병원에 문의해 주세요."; },
    correction: function (l) { return "[효자] 정정: 접수번호 " + l + " 앞서 보낸 호출 안내는 취소되었어요. 병원 안내를 확인해 주세요."; },
    delay: function (l) { return "[효자] 접수번호 " + l + " 진료가 지연되고 있어요. 병원 안내를 확인해 주세요."; }
  };
  function maybeNear(store, t, now) {
    if (t.status === "waiting" && t.ahead !== null && t.ahead <= store.cfg.NEAR_AHEAD) enqueue(store, t, "near", TEXT.near(t.label), now);
  }

  function validate(e, cfg) {
    if (!e || typeof e !== "object") return "invalid:event";
    if (typeof e.eventId !== "string" || !ID_RE.test(e.eventId)) return "invalid:eventId";
    if (!isInt(e.sequence) || e.sequence < 1) return "invalid:sequence";
    for (var k of ["hospitalId", "queueId", "ticketToken"]) if (typeof e[k] !== "string" || !ID_RE.test(e[k])) return "invalid:" + k;
    if (TYPES.indexOf(e.type) < 0) return "invalid:type";
    if (typeof e.observedAt !== "number" || !isFinite(e.observedAt)) return "invalid:observedAt";
    if (e.type === "waiting" || e.type === "queue_changed")
      if (!isInt(e.peopleAhead) || e.peopleAhead < 0 || e.peopleAhead > cfg.MAX_AHEAD) return "invalid:peopleAhead";
    return null;
  }

  // ctx: {now, authenticated} — authenticated는 어댑터가 서명 검증 뒤에만 true로 설정(이벤트 안의 값은 신뢰하지 않음)
  function ingest(store, e, ctx) {
    var cfg = store.cfg, now = ctx.now;
    if (ctx.authenticated !== true) return { accepted: false, reason: "unauthenticated" };
    var bad = validate(e, cfg);
    if (bad) return { accepted: false, reason: bad };
    var qk = qkey(e.hospitalId, e.queueId), tk = tkey(e.hospitalId, e.queueId, e.ticketToken);
    var q = store.queues[qk], t = store.tickets[tk];
    if (!q) return { accepted: false, reason: "unknown_queue" };
    if (!t) return { accepted: false, reason: "unknown_ticket" };
    if (q.seenSet[e.eventId]) return { accepted: false, reason: "duplicate_event" };
    if (q.blocked) return { accepted: false, reason: "queue_blocked_resync_needed" };
    if (e.sequence <= q.lastSeq) return { accepted: false, reason: "stale_sequence" };
    if (e.observedAt > now + cfg.MAX_SKEW_MS) return { accepted: false, reason: "future_observedAt" };
    if (t.observedAt !== null && e.observedAt < t.observedAt) return { accepted: false, reason: "older_observation" };
    var gap = e.sequence - q.lastSeq - 1;
    if (gap > cfg.MAX_SEQ_GAP) { q.blocked = true; return { accepted: false, reason: "gap_too_large" }; }
    // 수락 확정
    if (gap > 0) q.gapSeq = e.sequence;
    q.lastSeq = e.sequence;
    q.seenSet[e.eventId] = true; q.seen.push(e.eventId);
    if (q.seen.length > cfg.SEEN_CAP) delete q.seenSet[q.seen.shift()];
    t.lastEventAt = now;

    if (TERMINAL.indexOf(t.status) >= 0) {
      if (t.status === "called" && e.type === "cancelled") {
        var callMsg = t.outbox.filter(function (m) { return m.kind === "called"; })[0];
        voidPending(t);
        t.status = "cancelled"; t.observedAt = e.observedAt; t.syncSeq = e.sequence; t.ahead = null; t.estimate = null;
        if (callMsg && ["sent", "delivered", "unknown"].indexOf(callMsg.state) >= 0) enqueue(store, t, "correction", TEXT.correction(t.label), now);
        return { accepted: true, correction: true };
      }
      if (t.status === "called" && e.type === "completed") { t.status = "completed"; t.observedAt = e.observedAt; t.syncSeq = e.sequence; return { accepted: true }; }
      t.anomalies.push(e.type + "_after_" + t.status);
      return { accepted: false, reason: "terminal_state" };
    }

    t.observedAt = e.observedAt; t.syncSeq = e.sequence;
    switch (e.type) {
      case "waiting":
      case "queue_changed": {
        var prev = t.ahead;
        if (prev !== null && e.peopleAhead > prev) { t.movedBack = true; t.backFrom = prev; }
        else if (t.movedBack && e.peopleAhead < t.backFrom) { t.movedBack = false; }
        t.ahead = e.peopleAhead;
        var est = e.estimate, ok = est && isInt(est.min) && isInt(est.max) && est.min >= 0 && est.min <= est.max && est.max <= cfg.MAX_ETA_MIN;
        t.estimate = ok ? { min: est.min, max: est.max, basedOnAhead: e.peopleAhead, observedAt: e.observedAt } : null;
        if (e.type === "waiting" && t.status !== "waiting") t.status = "waiting";
        maybeNear(store, t, now);
        break;
      }
      case "paused": t.status = "paused"; t.estimate = null; break;
      case "resumed": t.status = "waiting"; maybeNear(store, t, now); break;
      case "delayed": t.status = "delayed"; t.estimate = null; enqueue(store, t, "delay", TEXT.delay(t.label), now); break;
      case "called": t.status = "called"; voidPending(t, ["near", "delay"]); enqueue(store, t, "called", TEXT.called(t.label), now); break;
      case "cancelled": t.status = "cancelled"; voidPending(t); enqueue(store, t, "cancelled", TEXT.cancelled(t.label), now); break;
      case "completed": t.status = "completed"; voidPending(t); break;
    }
    return { accepted: true };
  }

  // 관리자 재동기화(공급사 전체 상태 재수신 뒤): 큐 차단 해제
  function resync(store, h, q, seq) {
    var Q = store.queues[qkey(h, q)];
    if (!Q || !isInt(seq) || seq < Q.lastSeq) return false;
    Q.lastSeq = seq; Q.blocked = false; Q.gapSeq = seq; return true;
  }

  // 직원이 입력한 '현재 호출 번호'는 참고 표시일 뿐, 대기 인원 계산에 쓰지 않는다(우선진료·예약·진료실 변경 가능)
  function setCurrentCall(store, h, q, label, now) {
    var Q = store.queues[qkey(h, q)];
    if (!Q) return { ok: false, reason: "unknown_queue" };
    if (typeof label !== "string" || !LABEL_RE.test(label)) return { ok: false, reason: "invalid_label" };
    Q.currentCall = { label: label, at: now };
    return { ok: true };
  }

  function sweep(store, now) {
    var n = 0;
    Object.keys(store.tickets).forEach(function (k) {
      var t = store.tickets[k];
      if (TERMINAL.indexOf(t.status) < 0 && now - t.lastEventAt > store.cfg.EXPIRE_MS) { t.status = "expired"; voidPending(t); t.ahead = null; t.estimate = null; n++; }
    });
    return n;
  }

  function textStatus(t) {
    if (!t.consent) return "off";
    var live = t.outbox.filter(function (m) { return m.state !== "void"; });
    if (!live.length) return "none";
    if (live.some(function (m) { return m.state === "failed_final" || m.state === "unknown"; })) return "problem";
    if (live.every(function (m) { return m.state === "delivered"; })) return "delivered";
    return "pending";
  }

  function snapshot(store, h, q, token, now) {
    var t = store.tickets[tkey(h, q, token)];
    if (!t) return { found: false };
    var Q = store.queues[t.qk], cfg = store.cfg;
    var age = t.observedAt === null ? Infinity : Math.max(0, now - t.observedAt);
    var fresh = age <= cfg.MAX_AGE_MS;
    var degraded = Q.blocked || Q.gapSeq > t.syncSeq;
    var live = t.status === "waiting" && fresh && !degraded && t.ahead !== null;
    var out = { found: true, label: t.label, status: t.status, ahead: null, estimate: null, observedAt: t.observedAt, ageSec: age === Infinity ? null : Math.floor(age / 1000), fresh: fresh, degraded: degraded, textStatus: textStatus(t), alert: "" };
    var onsite = " 병원 현장 호출이 우선입니다.";
    if (t.status === "called") out.alert = "호출되었어요. 병원 안내에 따라 이동해 주세요.";
    else if (t.status === "cancelled") out.alert = "접수가 취소되었어요. 병원에 문의해 주세요.";
    else if (t.status === "completed") out.alert = "진료 순서가 끝났어요.";
    else if (t.status === "expired") out.alert = "접수 정보가 만료되었어요. 병원에 확인해 주세요.";
    else if (t.status === "paused") out.alert = "대기가 잠시 멈췄어요. 병원 안내를 확인해 주세요." ;
    else if (t.status === "delayed") out.alert = "진료가 지연되고 있어요. 병원 안내를 확인해 주세요.";
    else if (degraded) out.alert = "일부 갱신이 누락되었을 수 있어요. 병원 안내를 확인해 주세요." + onsite;
    else if (!fresh) out.alert = "정보 갱신이 지연되고 있어요. 병원 안내를 확인해 주세요." + onsite;
    else if (t.ahead === null) out.alert = "아직 순서 정보를 받지 못했어요." + onsite;
    else out.alert = t.movedBack ? "순서가 바뀌었어요. 병원 안내를 확인해 주세요." + onsite : "마지막 갱신 기준 정보예요." + onsite;
    var cc = Q.currentCall;
    out.currentCall = cc && now - cc.at <= cfg.MAX_AGE_MS * 5 ? { label: cc.label, ageSec: Math.floor(Math.max(0, now - cc.at) / 1000) } : null;
    if (live) {
      out.ahead = t.ahead;
      var e = t.estimate;
      if (e && !t.movedBack && e.basedOnAhead === t.ahead && e.observedAt === t.observedAt) out.estimate = { min: e.min, max: e.max };
    }
    return out;
  }

  // 발송 대상 조회: 발송 직전에 상태를 다시 확인(오래된/무효 문자 차단)
  function deliverable(store, now) {
    var cfg = store.cfg, list = [];
    Object.keys(store.tickets).forEach(function (k) {
      var t = store.tickets[k];
      t.outbox.forEach(function (m) {
        if (m.state !== "queued" && m.state !== "failed") return;
        if (m.nextAt > now) return;
        var ttl = m.kind === "near" ? cfg.NEAR_MSG_TTL_MS : cfg.CALL_MSG_TTL_MS;
        var invalid = (m.kind === "near" && t.status !== "waiting") || (m.kind === "called" && t.status !== "called") ||
          (m.kind === "delay" && t.status !== "delayed") || now - m.createdAt > ttl;
        if (invalid) { m.state = "void"; return; }
        list.push({ key: m.key, recipientRef: m.recipientRef, text: m.text });
      });
    });
    return list;
  }

  function markResult(store, key, result, now) {
    var cfg = store.cfg, found = null;
    Object.keys(store.tickets).forEach(function (k) { store.tickets[k].outbox.forEach(function (m) { if (m.key === key) found = m; }); });
    if (!found) return false;
    if (["delivered", "failed_final", "void"].indexOf(found.state) >= 0) return false;
    if (result === "sent") { found.state = "sent"; found.attempts++; }
    else if (result === "delivered") found.state = "delivered";
    else if (result === "unknown") { found.state = "unknown"; found.attempts++; } // 자동 재발송 금지(중복 방지) — 사람 확인
    else if (result === "failed") {
      found.attempts++;
      if (found.attempts >= cfg.MAX_ATTEMPTS) found.state = "failed_final";
      else { found.state = "failed"; found.nextAt = now + cfg.BACKOFF_MS * found.attempts; }
    } else return false;
    return true;
  }

  return { createStore: createStore, register: register, ingest: ingest, snapshot: snapshot, sweep: sweep, resync: resync, setCurrentCall: setCurrentCall,
    deliverable: deliverable, markResult: markResult, DEFAULTS: DEFAULTS, TYPES: TYPES, tkey: tkey };
});
