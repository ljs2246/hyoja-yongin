"use strict";
// 어댑터 모음 — 시험 전용. 네트워크 호출·실제 문자 발송·실제 키 사용 없음.
const crypto = require("node:crypto");
const Core = require("./queue-core.js");

// ── Track A: 공급사 웹훅 어댑터 (공급사 형식은 미확인 — 아래는 우리가 요구할 '제안 계약')
// 서명: HMAC-SHA256(secret, timestamp + "." + rawBody) 의 hex. 시각 허용 오차 5분.
function sign(secret, ts, rawBody) {
  return crypto.createHmac("sha256", secret).update(ts + "." + rawBody).digest("hex");
}
function verifyWebhook({ secret, headers, rawBody, now, toleranceMs = 300000 }) {
  const ts = headers["x-hyoja-timestamp"], sig = headers["x-hyoja-signature"];
  if (!secret || typeof ts !== "string" || typeof sig !== "string") return { ok: false, reason: "missing_signature" };
  const t = Number(ts);
  if (!Number.isFinite(t) || Math.abs(now - t) > toleranceMs) return { ok: false, reason: "timestamp_out_of_range" };
  const want = Buffer.from(sign(secret, ts, rawBody), "hex"), got = Buffer.from(sig, "hex");
  if (want.length !== got.length || !crypto.timingSafeEqual(want, got)) return { ok: false, reason: "bad_signature" };
  let body;
  try { body = JSON.parse(rawBody); } catch { return { ok: false, reason: "bad_json" }; }
  return { ok: true, body };
}
// 공급사 필드명이 확정되면 mapper만 바꾼다(핵심 엔진은 불변).
const proposedMapper = (b) => ({
  eventId: b.eventId, sequence: b.sequence, hospitalId: b.hospitalId, queueId: b.queueId, ticketToken: b.ticketToken,
  type: b.type, peopleAhead: b.peopleAhead, observedAt: b.observedAt, estimate: b.estimatedWait || undefined
});
function receiveWebhook(store, req, { secret, now, mapper = proposedMapper }) {
  const v = verifyWebhook({ secret, headers: req.headers, rawBody: req.rawBody, now });
  if (!v.ok) return { accepted: false, reason: v.reason };
  return Core.ingest(store, mapper(v.body), { now, authenticated: true });
}

// ── Track B: 효자 보드(병원 직원 입력). 단일 작성자 가정 — 직원 로그인·권한은 미구현(목)
function staffBoard(store, { hospitalId, queueId, staffAuthenticated }) {
  let counter = 0;
  return {
    emit(ticketToken, type, extra, now) {
      if (staffAuthenticated !== true) return { accepted: false, reason: "staff_not_authenticated" };
      const q = store.queues[hospitalId + "|" + queueId];
      if (!q) return { accepted: false, reason: "unknown_queue" };
      counter++;
      return Core.ingest(store, Object.assign({
        eventId: "staff-" + hospitalId + "-" + queueId + "-" + (q.lastSeq + 1) + "-" + counter,
        sequence: q.lastSeq + 1, hospitalId, queueId, ticketToken, type, observedAt: now
      }, extra || {}), { now, authenticated: true });
    }
  };
}

// ── 문자 게이트웨이 스텁: 항상 모의. 전화번호는 외부 보관소(resolver)에서만 얻고 로그에 남기지 않음
function dryRunGateway(store, now, resolver) {
  const results = [];
  for (const m of Core.deliverable(store, now)) {
    const phone = resolver(m.recipientRef);
    if (!phone) { Core.markResult(store, m.key, "failed", now); results.push({ key: m.key, result: "no_recipient" }); continue; }
    results.push({ key: m.key, result: "dry_run_not_sent", toMasked: phone.slice(0, 3) + "****" + phone.slice(-2) });
    // 모의 단계에서는 상태를 sent로 바꾸지 않는다 → 실제 발송 연동 전까지 큐에 남음
  }
  return results;
}

// ── NAVER Cloud SENS 요청 본문 생성기(발송하지 않음). 필드명은 공식 문서 대조 전(미검증).
function buildSensSmsPayload(msg, phone, { fromNumber }) {
  return {
    DRY_RUN_ONLY: true,
    type: "SMS", contentType: "COMM", countryCode: "82",
    from: fromNumber, content: msg.text,
    messages: [{ to: phone.replace(/-/g, "") }]
  };
}

module.exports = { sign, verifyWebhook, receiveWebhook, proposedMapper, staffBoard, dryRunGateway, buildSensSmsPayload };
