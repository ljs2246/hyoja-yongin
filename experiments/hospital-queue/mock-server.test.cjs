"use strict";
// 035번 설계안 시험 항목(QR-01~05, AUTH-01~05, QUEUE-01~03) 가상 데이터 시험. 실제 서버·계정 아님.
const test = require("node:test");
const assert = require("node:assert/strict");
const { createServer, CFG } = require("./mock-server.js");

function setup() {
  let t = 50_000_000;
  const clock = () => t; const adv = (ms) => { t += ms; };
  const s = createServer(clock);
  const pubA = s.addHospital("hospA", "가상의원A", { q1: "진료실 1", q2: "진료실 2" });
  const pubB = s.addHospital("hospB", "가상의원B", { q1: "진료실 1" });
  s.addStaff("opA1", "pw-test-1", "OPERATOR", "hospA", ["q1"]);
  s.addStaff("mgrA", "pw-test-2", "MANAGER", "hospA", []);
  s.addStaff("audA", "pw-test-3", "AUDITOR", "hospA", []);
  s.addStaff("opB1", "pw-test-4", "OPERATOR", "hospB", ["q1"]);
  const tok = (id, pw) => s.login(id, pw).token;
  return { s, adv, clock, pubA, pubB, tok };
}
function ticket(env, who = "opA1", pw = "pw-test-1", q = "q1", label = "A-023") {
  const token = env.tok(who, pw);
  const r = env.s.staffRegister(token, { queueId: q, label });
  assert.ok(r.ok, JSON.stringify(r));
  return { token, ticketToken: r.ticketToken, q, label };
}
const ids = (env) => env.s.publicIdsOf("hospA", "q1");

// ── AUTH
test("AUTH-01 로그인하지 않은 요청은 모든 변경을 거부", () => {
  const e = setup(); const tk = ticket(e);
  for (const r of [e.s.staffRegister(undefined, { queueId: "q1", label: "A-1" }), e.s.staffEmit("fake", { queueId: "q1", ticketToken: tk.ticketToken, type: "called", expectedVersion: 0 }),
    e.s.staffSetCurrentCall(null, { queueId: "q1", label: "A-1" }), e.s.staffIssueClaim("x", { queueId: "q1", ticketToken: tk.ticketToken })])
    assert.equal(r.error, "unauthenticated");
});
test("AUTH-02 다른 병원·다른 진료실 직원은 수정 불가", () => {
  const e = setup(); const tk = ticket(e);
  const b = e.tok("opB1", "pw-test-4");
  // 병원B 직원은 병원A 접수 토큰을 알아도 자기 병원 대기열에서만 찾으므로 적용되지 않음
  const r = e.s.staffEmit(b, { queueId: "q1", ticketToken: tk.ticketToken, type: "called", expectedVersion: 0 });
  assert.equal(r.ok, false); assert.ok(["unknown_queue", "unknown_ticket"].includes(r.error), r.error);
  const a1 = e.tok("opA1", "pw-test-1");
  assert.equal(e.s.staffRegister(a1, { queueId: "q2", label: "B-1" }).error, "forbidden"); // 배정되지 않은 진료실
  assert.equal(e.s.staffRegister(a1, { queueId: "q9", label: "B-1" }).error, "forbidden");
  const ps = e.s.redeemClaim(e.s.staffIssueClaim(a1, { queueId: "q1", ticketToken: tk.ticketToken }).code);
  assert.equal(e.s.myQueue(ps.token).view.status, "waiting"); // 병원B 직원 요청이 병원A 접수에 영향 없음
});
test("AUTH-03 로그아웃·유휴·절대 만료·계정 해지 후 세션 재사용 거부", () => {
  const e = setup();
  let t1 = e.tok("opA1", "pw-test-1"); e.s.logout(t1);
  assert.equal(e.s.staffRegister(t1, { queueId: "q1", label: "A-1" }).error, "unauthenticated");
  t1 = e.tok("opA1", "pw-test-1"); e.adv(CFG.IDLE_MS + 1);
  assert.equal(e.s.staffRegister(t1, { queueId: "q1", label: "A-1" }).error, "unauthenticated");
  t1 = e.tok("opA1", "pw-test-1");
  for (let i = 0; i < 40; i++) { e.adv(14 * 60000); if (!e.s.queueVersion(t1, "q1").ok) break; } // 계속 써도 8시간이면 끊김
  assert.equal(e.s.queueVersion(t1, "q1").ok, false);
  t1 = e.tok("opA1", "pw-test-1"); e.s.deactivate("opA1");
  assert.equal(e.s.staffRegister(t1, { queueId: "q1", label: "A-1" }).error, "unauthenticated");
  assert.equal(e.s.login("opA1", "pw-test-1").error, "bad_credentials");
});
test("AUTH-04 동시 수정은 버전 충돌로 한쪽만 적용, 중복 클릭은 거부", () => {
  const e = setup(); const tk = ticket(e);
  e.s.addStaff("opA1b", "pw-test-5", "OPERATOR", "hospA", ["q1"]);
  const x = e.tok("opA1", "pw-test-1"), y = e.tok("opA1b", "pw-test-5");
  const v = e.s.queueVersion(x, "q1").version;
  const r1 = e.s.staffEmit(x, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 4, expectedVersion: v });
  const r2 = e.s.staffEmit(y, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 1, expectedVersion: v });
  assert.equal(r1.ok, true); assert.equal(r2.error, "conflict");
  const r3 = e.s.staffEmit(x, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 4, expectedVersion: v }); // 같은 요청 재전송
  assert.equal(r3.error, "conflict");
});
test("AUTH-05 요청에 staffAuthenticated/verified/hospitalId를 넣어도 우회 불가", () => {
  const e = setup(); const tk = ticket(e);
  const r = e.s.staffEmit(undefined, { queueId: "q1", ticketToken: tk.ticketToken, type: "called", expectedVersion: 0, staffAuthenticated: true, verified: true, hospitalId: "hospA" });
  assert.equal(r.error, "unauthenticated");
  const b = e.tok("opB1", "pw-test-4");
  const r2 = e.s.staffRegister(b, { queueId: "q1", label: "X-1", hospitalId: "hospA" }); // 병원B 세션이 병원A인 척
  assert.equal(r2.ok, true);
  assert.equal(e.s.publicIdsOf("hospA", "q1") !== undefined, true);
  const mine = e.s.staffIssueClaim(e.tok("mgrA", "pw-test-2"), { queueId: "q1", ticketToken: tk.ticketToken });
  assert.equal(e.s.myQueue(e.s.redeemClaim(mine.code).token).view.label, "A-023"); // 병원A 대기열에 X-1이 생기지 않음
  assert.equal(Object.keys(e.s._S.store.tickets).filter((k) => k.startsWith("hospA|q1|")).length, 1);
});
test("AUTH-06 로그인 실패 반복 시 잠금, 로그인마다 새 세션 토큰", () => {
  const e = setup();
  for (let i = 0; i < CFG.LOGIN_MAX_FAILS; i++) assert.equal(e.s.login("opA1", "wrong").error, "bad_credentials");
  assert.equal(e.s.login("opA1", "pw-test-1").error, "locked");
  e.adv(CFG.LOGIN_LOCK_MS + 1);
  const a = e.s.login("opA1", "pw-test-1").token, b = e.s.login("opA1", "pw-test-1").token;
  assert.notEqual(a, b);
});
test("역할: AUDITOR는 수정 불가·익명 기록만, MANAGER는 상세 기록·수정 가능", () => {
  const e = setup(); const tk = ticket(e);
  const aud = e.tok("audA", "pw-test-3"), mgr = e.tok("mgrA", "pw-test-2");
  assert.equal(e.s.staffEmit(aud, { queueId: "q1", ticketToken: tk.ticketToken, type: "called", expectedVersion: 0 }).error, "forbidden");
  assert.equal(e.s.staffEmit(mgr, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 2, expectedVersion: 0 }).ok, true);
  const rows = e.s.auditView(aud).rows;
  assert.equal(rows.length, 1); assert.equal(rows[0].actorId, undefined); assert.equal(rows[0].eventId, undefined);
  assert.equal(e.s.auditView(mgr).rows[0].actorId, "mgrA");
  assert.equal(e.s.auditView(e.tok("opA1", "pw-test-1")).error, "forbidden");
  assert.equal(e.s.auditView(e.tok("opB1", "pw-test-4")).error, "forbidden");
});
test("감사 기록에 변경 전후·행위자·시각이 남음(거부된 시도 포함)", () => {
  const e = setup(); const tk = ticket(e); const x = tk.token;
  e.s.staffEmit(x, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 5, expectedVersion: 0 });
  e.s.staffEmit(x, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: -3, expectedVersion: 1 });
  const rows = e.s.auditView(e.tok("mgrA", "pw-test-2")).rows;
  assert.equal(rows.length, 2); assert.equal(rows[0].afterAhead, 5); assert.equal(rows[1].accepted, false); assert.match(rows[1].reason, /invalid:peopleAhead/);
});

// ── QR
test("QR-01 공용 QR 화면에는 개인 접수번호·환자 정보가 없음", () => {
  const e = setup(); const tk = ticket(e);
  e.s.staffEmit(tk.token, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 2, expectedVersion: 0 });
  e.s.staffSetCurrentCall(tk.token, { queueId: "q1", label: "A-020" });
  const { hospitalPublicId, queuePublicId } = ids(e);
  const v = e.s.publicQueueView(hospitalPublicId, queuePublicId);
  assert.equal(v.currentCall.label, "A-020");
  const txt = JSON.stringify(v);
  assert.doesNotMatch(txt, /A-023|peopleAhead|ahead|ticket|tok/);
  assert.equal(e.s.publicQueueView("nope", "nope").error, "not_found");
  assert.notEqual(hospitalPublicId, "hospA"); // 내부 ID와 다른 공개 별칭
});
test("QR-02 일회용 코드: 재사용·만료·위조 거부", () => {
  const e = setup(); const tk = ticket(e);
  const c = e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken });
  assert.ok(c.code.length >= 32); // 192비트 난수
  assert.equal(e.s.redeemClaim(c.code).ok, true);
  assert.equal(e.s.redeemClaim(c.code).error, "already_used");
  assert.equal(e.s.redeemClaim(c.code + "x").error, "invalid_code");
  assert.equal(e.s.redeemClaim("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA").error, "invalid_code");
  const c2 = e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken });
  e.adv(CFG.CLAIM_TTL_MS + 1);
  assert.equal(e.s.redeemClaim(c2.code).error, "expired");
});
test("QR-02b 코드는 저장소에 해시로만 보관(원문 노출 없음)", () => {
  const e = setup(); const tk = ticket(e);
  const c = e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken });
  assert.equal(JSON.stringify(Object.keys(e.s._S.claims)).includes(c.code), false);
});
test("QR-03 접수번호만 입력하면 상태를 보여주지 않고, PIN 오입력은 횟수 제한 후 잠금", () => {
  const e = setup(); const tk = ticket(e);
  const c = e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken });
  assert.equal(e.s.lookupByNumber("A-023").error, "pin_required");
  assert.equal(e.s.lookupByNumber("A-023", "").error, "pin_required");
  for (let i = 0; i < CFG.PIN_MAX_FAILS; i++) assert.equal(e.s.lookupByNumber("A-023", "000000" === c.pin ? "111111" : "000000").error, "invalid_pin");
  assert.equal(e.s.lookupByNumber("A-023", c.pin).error, "locked"); // 맞는 PIN도 잠금 중에는 거부
  e.adv(CFG.PIN_LOCK_MS + 1);
  const c2 = e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken });
  assert.equal(e.s.lookupByNumber("A-023", c2.pin).ok, true);
});
test("QR-04 취소·완료·권한 해지 시 환자 세션 폐기", () => {
  const e = setup(); const tk = ticket(e);
  const mk = () => e.s.redeemClaim(e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken }).code).token;
  let p = mk();
  e.s.staffEmit(tk.token, { queueId: "q1", ticketToken: tk.ticketToken, type: "cancelled", expectedVersion: 0 });
  const last = e.s.myQueue(p);
  assert.equal(last.final, true); assert.equal(last.view.status, "cancelled"); assert.match(last.view.alert, /취소/);
  assert.equal(e.s.myQueue(p).error, "no_session"); // 한 번 알려주고 폐기
  const tk2 = ticket(e, "opA1", "pw-test-1", "q1", "A-024");
  const p2 = e.s.redeemClaim(e.s.staffIssueClaim(tk2.token, { queueId: "q1", ticketToken: tk2.ticketToken }).code).token;
  assert.equal(e.s.staffRevokePatient(tk2.token, { queueId: "q1", ticketToken: tk2.ticketToken }).revoked, 1);
  assert.equal(e.s.myQueue(p2).error, "no_session");
  const tk3 = ticket(e, "opA1", "pw-test-1", "q1", "A-025");
  const p3 = e.s.redeemClaim(e.s.staffIssueClaim(tk3.token, { queueId: "q1", ticketToken: tk3.ticketToken }).code).token;
  e.adv(CFG.PATIENT_SESSION_MS + 1);
  assert.equal(e.s.myQueue(p3).error, "session_expired");
});
test("QR-05 주소·로그 문자열에서 토큰 가림, 환자 응답에 내부 정보 없음", () => {
  const e = setup(); const tk = ticket(e);
  assert.equal(e.s.maskToken("GET /v1/claim/AbCdEf123456_-xyz HTTP/1.1"), "GET /v1/claim/**** HTTP/1.1");
  const c = e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken });
  const r = e.s.myQueue(e.s.redeemClaim(c.code).token);
  assert.doesNotMatch(JSON.stringify(r), /hospA|hospB|q1|tok|opA1|queue_changed|outbox|recipient/);
  assert.equal(Object.keys(r.view).includes("ticketToken"), false);
});
test("환자 세션은 자기 접수만 본다(다른 환자 접수 노출 없음)", () => {
  const e = setup(); const t1 = ticket(e), t2 = ticket(e, "opA1", "pw-test-1", "q1", "A-024");
  e.s.staffEmit(t2.token, { queueId: "q1", ticketToken: t2.ticketToken, type: "queue_changed", peopleAhead: 1, expectedVersion: 0 });
  const p1 = e.s.redeemClaim(e.s.staffIssueClaim(t1.token, { queueId: "q1", ticketToken: t1.ticketToken }).code).token;
  const v = e.s.myQueue(p1).view; assert.equal(v.label, "A-023"); assert.equal(v.ahead, null);
});

// ── QUEUE
test("QUEUE-01 현재 호출 번호만 입력하면 '앞 N명'은 표시되지 않음(번호 차이로 계산 안 함)", () => {
  const e = setup(); const tk = ticket(e);
  e.s.staffSetCurrentCall(tk.token, { queueId: "q1", label: "A-020" });
  const p = e.s.redeemClaim(e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken }).code).token;
  const v = e.s.myQueue(p).view; assert.equal(v.ahead, null); assert.equal(v.currentCall.label, "A-020");
});
test("QUEUE-02 갱신이 오래되면 환자 화면의 인원·예상시간 숨김", () => {
  const e = setup(); const tk = ticket(e);
  e.s.staffEmit(tk.token, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 3, expectedVersion: 0 });
  const p = e.s.redeemClaim(e.s.staffIssueClaim(tk.token, { queueId: "q1", ticketToken: tk.ticketToken }).code).token;
  assert.equal(e.s.myQueue(p).view.ahead, 3);
  e.adv(3 * 60000);
  const v = e.s.myQueue(p).view; assert.equal(v.ahead, null); assert.match(v.alert, /지연/);
});
test("QUEUE-03 취소 뒤 호출은 서버가 거부, 환자에게 호출로 보이지 않음", () => {
  const e = setup(); const tk = ticket(e);
  assert.equal(e.s.staffEmit(tk.token, { queueId: "q1", ticketToken: tk.ticketToken, type: "cancelled", expectedVersion: 0 }).ok, true);
  assert.equal(e.s.staffEmit(tk.token, { queueId: "q1", ticketToken: tk.ticketToken, type: "called", expectedVersion: 1 }).error, "terminal_state");
});
test("서버가 이벤트 ID·순번·관측 시각을 만든다(클라이언트 값 무시)", () => {
  const e = setup(); const tk = ticket(e);
  e.s.staffEmit(tk.token, { queueId: "q1", ticketToken: tk.ticketToken, type: "queue_changed", peopleAhead: 2, expectedVersion: 0, eventId: "evil", sequence: 999999, observedAt: 1 });
  const rows = e.s.auditView(e.tok("mgrA", "pw-test-2")).rows;
  assert.notEqual(rows[0].eventId, "evil"); assert.equal(rows[0].accepted, true);
});
