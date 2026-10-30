"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const Core = require("./queue-core.js");
const A = require("./adapters.js");
const T = 20_000_000, SECRET = "test-secret-not-real";
function store() {
  const s = Core.createStore();
  Core.register(s, { hospitalId: "h1", queueId: "q1", ticketToken: "t1", label: "A-001", consent: true, recipientRef: "r1" }, T);
  return s;
}
function req(body, { secret = SECRET, ts = T, tamper = false } = {}) {
  const raw = JSON.stringify(body);
  return { rawBody: tamper ? raw.replace('"peopleAhead":2', '"peopleAhead":0') : raw,
    headers: { "x-hyoja-timestamp": String(ts), "x-hyoja-signature": A.sign(secret, String(ts), raw) } };
}
const body = { eventId: "w1", sequence: 1, hospitalId: "h1", queueId: "q1", ticketToken: "t1", type: "queue_changed", peopleAhead: 2, observedAt: T };

test("올바른 서명의 웹훅은 수락", () => {
  const s = store();
  assert.equal(A.receiveWebhook(s, req(body), { secret: SECRET, now: T }).accepted, true);
});
test("서명 불일치·본문 변조·헤더 누락·시각 초과·잘못된 JSON 모두 거부", () => {
  const s = store();
  assert.equal(A.receiveWebhook(s, req(body, { secret: "other" }), { secret: SECRET, now: T }).reason, "bad_signature");
  assert.equal(A.receiveWebhook(s, req(body, { tamper: true }), { secret: SECRET, now: T }).reason, "bad_signature");
  assert.equal(A.receiveWebhook(s, { rawBody: "{}", headers: {} }, { secret: SECRET, now: T }).reason, "missing_signature");
  assert.equal(A.receiveWebhook(s, req(body, { ts: T - 600000 }), { secret: SECRET, now: T }).reason, "timestamp_out_of_range");
  const raw = "{not json", ts = String(T);
  assert.equal(A.receiveWebhook(s, { rawBody: raw, headers: { "x-hyoja-timestamp": ts, "x-hyoja-signature": A.sign(SECRET, ts, raw) } }, { secret: SECRET, now: T }).reason, "bad_json");
  assert.equal(Core.snapshot(s, "h1", "q1", "t1", T).ahead, null);
});
test("같은 웹훅 재전송(공급사 재시도)은 문자를 늘리지 않음", () => {
  const s = store();
  A.receiveWebhook(s, req(body), { secret: SECRET, now: T });
  assert.equal(A.receiveWebhook(s, req(body), { secret: SECRET, now: T }).reason, "duplicate_event");
  assert.equal(s.tickets["h1|q1|t1"].outbox.length, 1);
});
test("공급사 본문의 verified 필드는 효력 없음(서명만이 인증)", () => {
  const s = store();
  A.receiveWebhook(s, req({ ...body, verified: true, estimatedWait: { min: 5, max: 9 } }), { secret: SECRET, now: T });
  assert.deepEqual(Core.snapshot(s, "h1", "q1", "t1", T).estimate, { min: 5, max: 9 }); // 서명 통과 이벤트의 예상시간은 병원 책임 데이터
  const s2 = store();
  A.receiveWebhook(s2, req({ ...body, verified: true, estimatedWait: { min: 5, max: 9 } }, { secret: "x" }), { secret: SECRET, now: T });
  assert.equal(Core.snapshot(s2, "h1", "q1", "t1", T).estimate, null);
});
test("직원 보드: 로그인 없으면 거부, 있으면 순번 자동 증가", () => {
  const s = store();
  assert.equal(A.staffBoard(s, { hospitalId: "h1", queueId: "q1", staffAuthenticated: false }).emit("t1", "called", {}, T).reason, "staff_not_authenticated");
  const b = A.staffBoard(s, { hospitalId: "h1", queueId: "q1", staffAuthenticated: true });
  assert.equal(b.emit("t1", "queue_changed", { peopleAhead: 5 }, T).accepted, true);
  assert.equal(b.emit("t1", "queue_changed", { peopleAhead: 4 }, T + 1000).accepted, true);
  assert.equal(Core.snapshot(s, "h1", "q1", "t1", T + 1000).ahead, 4);
});
test("직원 보드: 모르는 접수번호는 새로 만들지 않음", () => {
  const s = store();
  const b = A.staffBoard(s, { hospitalId: "h1", queueId: "q1", staffAuthenticated: true });
  assert.equal(b.emit("typo", "called", {}, T).reason, "unknown_ticket");
});
test("모의 게이트웨이는 발송하지 않고 번호를 가려서만 기록, SENS 본문은 DRY_RUN 표시", () => {
  const s = store();
  const b = A.staffBoard(s, { hospitalId: "h1", queueId: "q1", staffAuthenticated: true });
  b.emit("t1", "queue_changed", { peopleAhead: 2 }, T);
  const r = A.dryRunGateway(s, T, (ref) => (ref === "r1" ? "010-0000-0000" : null));
  assert.equal(r[0].result, "dry_run_not_sent");
  assert.doesNotMatch(JSON.stringify(r), /010-0000-0000/);
  assert.equal(s.tickets["h1|q1|t1"].outbox[0].state, "queued");
  const p = A.buildSensSmsPayload({ text: "x" }, "010-0000-0000", { fromNumber: "00000000000" });
  assert.equal(p.DRY_RUN_ONLY, true);
});
test("수신자 정보를 못 찾으면 실패로 기록(엉뚱한 번호로 보내지 않음)", () => {
  const s = store();
  A.staffBoard(s, { hospitalId: "h1", queueId: "q1", staffAuthenticated: true }).emit("t1", "queue_changed", { peopleAhead: 2 }, T);
  const r = A.dryRunGateway(s, T, () => null);
  assert.equal(r[0].result, "no_recipient");
  assert.equal(s.tickets["h1|q1|t1"].outbox[0].state, "failed");
});
