"use strict";
// 서버 로직 모의 구현 — 035번 설계안(QR 권한·직원 로그인·역할별 권한)을 가상 데이터로 시험하기 위한 것.
// 네트워크·HTTP·실제 계정·실제 환자 정보 없음. 운영 코드로 쓰지 말 것(저장소·HTTPS·감사 저장 미구현).
const crypto = require("node:crypto");
const Core = require("./queue-core.js");

const CFG = {
  IDLE_MS: 15 * 60000, ABS_MS: 8 * 3600000, LOGIN_MAX_FAILS: 5, LOGIN_LOCK_MS: 15 * 60000,
  CLAIM_TTL_MS: 5 * 60000, PATIENT_SESSION_MS: 6 * 3600000, PIN_MAX_FAILS: 5, PIN_LOCK_MS: 10 * 60000
};
const rnd = (n = 32) => crypto.randomBytes(n).toString("base64url");
const sha = (s) => crypto.createHash("sha256").update(s).digest("hex");
const hashPw = (pw, salt) => crypto.scryptSync(pw, salt, 32).toString("hex");

function createServer(clock = Date.now) {
  const S = {
    store: Core.createStore(), accounts: {}, sessions: {}, patientSessions: {}, claims: {}, pins: {},
    fails: {}, pinFails: {}, audit: [], hospitals: {}, publicMap: {}, versions: {}, seq: 0
  };
  const now = () => clock();
  const err = (code) => ({ ok: false, error: code });

  // ── 관리 준비(가상): 병원·진료실·직원 등록
  function addHospital(id, name, queues) {
    const pub = "H" + rnd(6);
    S.hospitals[id] = { name, queues: {} };
    S.publicMap[pub] = { hospitalId: id, queues: {} };
    Object.keys(queues).forEach((qid) => {
      const qp = "Q" + rnd(6);
      S.hospitals[id].queues[qid] = queues[qid];
      S.publicMap[pub].queues[qp] = qid;
      S.versions[id + "|" + qid] = 0;
    });
    return pub;
  }
  function publicIdsOf(hospitalId, queueId) {
    for (const [pub, h] of Object.entries(S.publicMap)) if (h.hospitalId === hospitalId)
      for (const [qp, q] of Object.entries(h.queues)) if (q === queueId) return { hospitalPublicId: pub, queuePublicId: qp };
  }
  function addStaff(accountId, secret, role, hospitalId, queueIds) {
    const salt = rnd(8);
    S.accounts[accountId] = { role, hospitalId, queueIds: queueIds || [], salt, hash: hashPw(secret, salt), active: true };
  }
  function deactivate(accountId) {
    if (S.accounts[accountId]) S.accounts[accountId].active = false;
    Object.keys(S.sessions).forEach((t) => { if (S.sessions[t].accountId === accountId) delete S.sessions[t]; });
  }

  // ── 직원 로그인
  function login(accountId, secret) {
    const t = now(), f = S.fails[accountId] || { n: 0, until: 0 };
    if (f.until > t) return err("locked");
    const a = S.accounts[accountId];
    const ok = a && a.active && crypto.timingSafeEqual(Buffer.from(hashPw(secret, a.salt), "hex"), Buffer.from(a.hash, "hex"));
    if (!ok) {
      f.n++; if (f.n >= CFG.LOGIN_MAX_FAILS) { f.until = t + CFG.LOGIN_LOCK_MS; f.n = 0; }
      S.fails[accountId] = f; return err("bad_credentials");
    }
    S.fails[accountId] = { n: 0, until: 0 };
    const token = rnd(32); // 로그인마다 새 세션(세션 고정 방지)
    S.sessions[token] = { accountId, createdAt: t, lastAt: t };
    return { ok: true, token };
  }
  function logout(token) { delete S.sessions[token]; return { ok: true }; }
  function auth(token) {
    const s = S.sessions[token]; if (!s) return null;
    const t = now(), a = S.accounts[s.accountId];
    if (!a || !a.active || t - s.lastAt > CFG.IDLE_MS || t - s.createdAt > CFG.ABS_MS) { delete S.sessions[token]; return null; }
    s.lastAt = t; return { accountId: s.accountId, ...a };
  }
  const canWrite = (a, qid) => (a.role === "OPERATOR" && a.queueIds.includes(qid)) || a.role === "MANAGER";
  const inHospital = (a, qid) => !!S.hospitals[a.hospitalId] && qid in S.hospitals[a.hospitalId].queues;

  // 직원 요청의 병원은 세션에서만 결정한다. 요청 본문의 hospitalId·staffAuthenticated·verified 는 무시한다.
  function staffRegister(token, req) {
    const a = auth(token); if (!a) return err("unauthenticated");
    if (!inHospital(a, req.queueId) || !canWrite(a, req.queueId)) return err("forbidden");
    const ticketToken = "t" + crypto.randomBytes(12).toString("hex");
    const r = Core.register(S.store, { hospitalId: a.hospitalId, queueId: req.queueId, ticketToken, label: req.label, consent: false, baseSeq: S.store.queues[a.hospitalId + "|" + req.queueId] ? undefined : 0 }, now());
    return r.ok ? { ok: true, ticketToken } : err(r.reason);
  }
  function staffEmit(token, req) {
    const a = auth(token); if (!a) return err("unauthenticated");
    if (!inHospital(a, req.queueId) || !canWrite(a, req.queueId)) return err("forbidden");
    const vk = a.hospitalId + "|" + req.queueId;
    if (req.expectedVersion !== S.versions[vk]) return err("conflict"); // 동시 수정 충돌
    const Q = S.store.queues[vk]; if (!Q) return err("unknown_queue");
    const before = Core.snapshot(S.store, a.hospitalId, req.queueId, req.ticketToken, now());
    const ev = { eventId: "srv-" + (++S.seq) + "-" + rnd(6), sequence: Q.lastSeq + 1, hospitalId: a.hospitalId, queueId: req.queueId,
      ticketToken: req.ticketToken, type: req.type, observedAt: now(), peopleAhead: req.peopleAhead };
    const r = Core.ingest(S.store, ev, { now: now(), authenticated: true });
    S.audit.push({ actorId: a.accountId, eventId: ev.eventId, queue: vk, type: req.type, accepted: r.accepted, reason: r.reason || null,
      beforeAhead: before.ahead, afterAhead: req.peopleAhead === undefined ? null : req.peopleAhead, at: now() });
    if (r.accepted) S.versions[vk]++;
    return r.accepted ? { ok: true, version: S.versions[vk] } : err(r.reason);
  }
  function staffSetCurrentCall(token, req) {
    const a = auth(token); if (!a) return err("unauthenticated");
    if (!inHospital(a, req.queueId) || !canWrite(a, req.queueId)) return err("forbidden");
    const r = Core.setCurrentCall(S.store, a.hospitalId, req.queueId, req.label, now());
    return r.ok ? { ok: true } : err(r.reason);
  }
  function queueVersion(token, queueId) {
    const a = auth(token); if (!a || !inHospital(a, queueId)) return err("forbidden");
    return { ok: true, version: S.versions[a.hospitalId + "|" + queueId] };
  }
  function auditView(token) {
    const a = auth(token); if (!a) return err("unauthenticated");
    if (a.role !== "MANAGER" && a.role !== "AUDITOR") return err("forbidden");
    const own = a.hospitalId + "|";
    // 감사 담당은 행위자·티켓 식별 없이 익명화한 기록만 읽는다.
    return { ok: true, rows: S.audit.filter((r) => r.queue.startsWith(own)).map((r) => a.role === "AUDITOR"
      ? { queue: r.queue, type: r.type, accepted: r.accepted, at: r.at } : r) };
  }

  // ── 공용 QR: 개인 정보 없음
  function publicQueueView(hospitalPublicId, queuePublicId) {
    const h = S.publicMap[hospitalPublicId]; const qid = h && h.queues[queuePublicId];
    if (!qid) return err("not_found");
    const Q = S.store.queues[h.hospitalId + "|" + qid], t = now();
    const cc = Q && Q.currentCall && t - Q.currentCall.at <= Core.DEFAULTS.MAX_AGE_MS * 5 ? { label: Q.currentCall.label, ageSec: Math.floor((t - Q.currentCall.at) / 1000) } : null;
    return { ok: true, hospitalName: S.hospitals[h.hospitalId].name, queueName: S.hospitals[h.hospitalId].queues[qid],
      currentCall: cc, note: "병원 현장 호출이 우선이에요." };
  }

  // ── 개인 QR/PIN: 1회용·짧은 만료·서버에서 소각
  function staffIssueClaim(token, req) {
    const a = auth(token); if (!a) return err("unauthenticated");
    if (!inHospital(a, req.queueId) || !canWrite(a, req.queueId)) return err("forbidden");
    const tk = Core.tkey(a.hospitalId, req.queueId, req.ticketToken);
    if (!S.store.tickets[tk]) return err("unknown_ticket");
    const code = rnd(24); // 192비트
    const pin = String(crypto.randomInt(0, 1000000)).padStart(6, "0");
    const rec = { tk, exp: now() + CFG.CLAIM_TTL_MS, used: false, label: S.store.tickets[tk].label, pinHash: sha(pin) };
    S.claims[sha(code)] = rec;
    S.pins[tk] = S.pins[tk] || []; S.pins[tk].push(rec);
    return { ok: true, code, pin, expiresInSec: CFG.CLAIM_TTL_MS / 1000 };
  }
  function startPatientSession(rec) {
    rec.used = true;
    const token = rnd(32); S.patientSessions[token] = { tk: rec.tk, createdAt: now() };
    return { ok: true, token };
  }
  function redeemClaim(code) {
    const rec = S.claims[sha(String(code))];
    if (!rec) return err("invalid_code");
    if (rec.used) return err("already_used");
    if (now() > rec.exp) return err("expired");
    return startPatientSession(rec);
  }
  // QR 없이 접수번호 + 접수증 PIN. 접수번호만으로는 절대 상태를 보여주지 않는다.
  function lookupByNumber(label, pin) {
    const f = S.pinFails[label] || { n: 0, until: 0 };
    if (f.until > now()) return err("locked");
    if (typeof pin !== "string" || !/^\d{6}$/.test(pin)) return err("pin_required");
    for (const recs of Object.values(S.pins)) for (const rec of recs) {
      if (rec.label === label && !rec.used && now() <= rec.exp && rec.pinHash === sha(pin)) { S.pinFails[label] = { n: 0, until: 0 }; return startPatientSession(rec); }
    }
    f.n++; if (f.n >= CFG.PIN_MAX_FAILS) { f.until = now() + CFG.PIN_LOCK_MS; f.n = 0; }
    S.pinFails[label] = f; return err("invalid_pin");
  }
  function myQueue(patientToken) {
    const ps = S.patientSessions[patientToken];
    if (!ps) return err("no_session");
    if (now() - ps.createdAt > CFG.PATIENT_SESSION_MS) { delete S.patientSessions[patientToken]; return err("session_expired"); }
    const t = S.store.tickets[ps.tk]; if (!t) return err("no_session");
    const [h, q, tok] = ps.tk.split("|");
    const snap = Core.snapshot(S.store, h, q, tok, now());
    const final = ["cancelled", "completed", "expired"].includes(snap.status);
    if (final) delete S.patientSessions[patientToken]; // 종료된 접수는 한 번 알려주고 세션 폐기
    // 환자에게는 자기 접수 상태만(병원·직원 내부 정보 없음)
    return { ok: true, final, view: { label: snap.label, status: snap.status, ahead: snap.ahead, estimate: snap.estimate, ageSec: snap.ageSec, alert: snap.alert, currentCall: snap.currentCall } };
  }
  function staffRevokePatient(token, req) {
    const a = auth(token); if (!a) return err("unauthenticated");
    if (!inHospital(a, req.queueId) || !canWrite(a, req.queueId)) return err("forbidden");
    const tk = Core.tkey(a.hospitalId, req.queueId, req.ticketToken); let n = 0;
    Object.keys(S.patientSessions).forEach((k) => { if (S.patientSessions[k].tk === tk) { delete S.patientSessions[k]; n++; } });
    (S.pins[tk] || []).forEach((r) => { r.used = true; });
    return { ok: true, revoked: n };
  }
  // 사람이 쓰는 문자열(주소·로그)에서 토큰을 가린다
  function maskToken(s) { return String(s).replace(/(claim\/|my-queue\?t=)[A-Za-z0-9_-]{6,}/g, "$1****"); }

  return { addHospital, addStaff, deactivate, login, logout, staffRegister, staffEmit, staffSetCurrentCall, queueVersion, auditView,
    publicQueueView, staffIssueClaim, redeemClaim, lookupByNumber, myQueue, staffRevokePatient, maskToken, publicIdsOf, _S: S, CFG };
}
module.exports = { createServer, CFG };
