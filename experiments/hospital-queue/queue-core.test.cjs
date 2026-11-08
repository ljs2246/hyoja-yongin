"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const Q = require("./queue-core.js");
const T = 10_000_000;
const H = "hospA", QU = "q1", TK = "tok1";
let n = 0;
function mk(extra = {}, opts) {
  const s = Q.createStore(opts);
  const r = Q.register(s, { hospitalId: H, queueId: QU, ticketToken: TK, label: "A-023", consent: true, recipientRef: "r1", baseSeq: 0, ...extra }, T);
  assert.ok(r.ok, JSON.stringify(r));
  return s;
}
function ev(s, type, extra = {}, now = T, o = {}) {
  const q = s.queues[`${H}|${QU}`];
  const e = { eventId: "e" + ++n, sequence: q.lastSeq + 1, hospitalId: H, queueId: QU, ticketToken: TK, type, observedAt: now, ...extra };
  return Q.ingest(s, Object.assign(e, o.override || {}), { now, authenticated: o.auth !== false });
}
const snap = (s, now = T) => Q.snapshot(s, H, QU, TK, now);
const msgs = (s, kind) => s.tickets[Q.tkey(H, QU, TK)].outbox.filter(m => !kind || m.kind === kind);

// ── 위험 1: 중복 접수·중복 문자
test("같은 접수 재등록은 중복으로 처리하고 문자 수신자를 늘리지 않음", () => {
  const s = mk();
  const r = Q.register(s, { hospitalId: H, queueId: QU, ticketToken: TK, label: "A-023", consent: true, recipientRef: "r1" }, T);
  assert.equal(r.duplicate, true);
  assert.equal(Object.keys(s.tickets).length, 1);
});
test("같은 수신자가 다른 토큰으로 이중 접수하면 거부", () => {
  const s = mk();
  const r = Q.register(s, { hospitalId: H, queueId: QU, ticketToken: "tok2", label: "A-024", consent: true, recipientRef: "r1" }, T);
  assert.equal(r.reason, "duplicate_recipient");
});
test("같은 이벤트 ID 재수신은 문자를 다시 만들지 않음", () => {
  const s = mk();
  const e = { eventId: "dup1", sequence: 1, hospitalId: H, queueId: QU, ticketToken: TK, type: "queue_changed", peopleAhead: 2, observedAt: T };
  assert.equal(Q.ingest(s, e, { now: T, authenticated: true }).accepted, true);
  assert.equal(Q.ingest(s, { ...e, sequence: 2 }, { now: T, authenticated: true }).reason, "duplicate_event");
  assert.equal(msgs(s, "near").length, 1);
});
test("3명 이하 안내는 한 번만, 숫자 없이(오래된 숫자 방지)", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 3 }); ev(s, "queue_changed", { peopleAhead: 2 }); ev(s, "queue_changed", { peopleAhead: 1 });
  assert.equal(msgs(s, "near").length, 1);
  assert.doesNotMatch(msgs(s, "near")[0].text, /\d명/);
});
test("문자 총 개수 상한 초과 시 추가 생성 안 함", () => {
  const s = mk({}, { MAX_MSGS: 2 });
  ev(s, "queue_changed", { peopleAhead: 2 }); ev(s, "delayed");
  msgs(s).forEach(m => Q.markResult(s, m.key, "sent", T)); // 이미 나간 문자는 취소할 수 없음
  ev(s, "called");
  assert.equal(msgs(s).filter(m => m.state !== "void").length, 2); // 상한 2건에서 정지
});
test("문자 동의 없으면 화면은 되고 문자는 0건", () => {
  const s = mk({ consent: false, recipientRef: undefined });
  ev(s, "queue_changed", { peopleAhead: 1 });
  assert.equal(msgs(s).length, 0); assert.equal(snap(s).ahead, 1); assert.equal(snap(s).textStatus, "off");
});

// ── 위험 2: 순번 뒤로 감
test("대기 인원이 늘어나면 '순서 바뀜' 표시 + 예상시간 숨김", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2, estimate: { min: 5, max: 10 } });
  ev(s, "queue_changed", { peopleAhead: 5, estimate: { min: 5, max: 10 } });
  const v = snap(s);
  assert.match(v.alert, /순서가 바뀌었어요/); assert.equal(v.estimate, null); assert.equal(v.ahead, 5);
});
test("뒤로 갔다가 원래보다 줄면 경고 해제", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 }); ev(s, "queue_changed", { peopleAhead: 5 }); ev(s, "queue_changed", { peopleAhead: 1 });
  assert.doesNotMatch(snap(s).alert, /바뀌었어요/);
});

// ── 위험 3: 오래된 정보
test("관측 시각 기준 2분 초과면 숫자 숨김(수신 시각이 아님)", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 }, T, { override: { observedAt: T - 200000 } });
  assert.equal(snap(s).ahead, null); assert.match(snap(s).alert, /갱신이 지연/);
});
test("미래 관측 시각(시계 오차 초과)은 거부", () => {
  const s = mk();
  assert.equal(ev(s, "queue_changed", { peopleAhead: 2 }, T, { override: { observedAt: T + 60000 } }).reason, "future_observedAt");
});
test("더 오래된 관측 시각 이벤트는 순서번호가 커도 거부", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 4 }, T, { override: { observedAt: T } });
  assert.equal(ev(s, "queue_changed", { peopleAhead: 1 }, T, { override: { observedAt: T - 5000 } }).reason, "older_observation");
  assert.equal(snap(s).ahead, 4);
});
test("순서번호 누락(작은 틈)은 해당 화면 숫자를 숨기고 다음 이벤트로 회복", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 5 });
  const q = s.queues[`${H}|${QU}`];
  ev(s, "queue_changed", { peopleAhead: 4 }, T, { override: { sequence: q.lastSeq + 3 } });
  assert.equal(snap(s).degraded, false); // 이 티켓은 틈 이벤트 자체를 받았으므로 동기화됨
  // 다른 환자 이벤트 누락 시뮬레이션: 큐 틈만 생기고 이 티켓 이벤트가 없으면 숨김
  q.gapSeq = q.lastSeq + 1; q.lastSeq += 1;
  assert.equal(snap(s).ahead, null); assert.match(snap(s).alert, /누락/);
  ev(s, "queue_changed", { peopleAhead: 3 });
  assert.equal(snap(s).ahead, 3);
});
test("큰 순서번호 점프는 큐 차단, 재동기화 전 모든 이벤트 거부", () => {
  const s = mk();
  const q = s.queues[`${H}|${QU}`];
  assert.equal(ev(s, "queue_changed", { peopleAhead: 1 }, T, { override: { sequence: q.lastSeq + 9999 } }).reason, "gap_too_large");
  assert.equal(ev(s, "queue_changed", { peopleAhead: 1 }).reason, "queue_blocked_resync_needed");
  assert.equal(snap(s).degraded, true);
  assert.equal(Q.resync(s, H, QU, q.lastSeq), true);
  assert.equal(ev(s, "queue_changed", { peopleAhead: 1 }).accepted, true);
});
test("6시간 무소식 접수는 만료되고 문자 대기분 취소", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 });
  assert.equal(Q.sweep(s, T + 7 * 3600000), 1);
  assert.equal(snap(s, T + 7 * 3600000).status, "expired");
  assert.equal(Q.deliverable(s, T + 7 * 3600000).length, 0);
});

// ── 위험 4: 취소 뒤 잘못된 호출 / 호출 뒤 취소
test("취소 뒤 호출 이벤트는 거부되고 호출 문자 없음", () => {
  const s = mk();
  ev(s, "cancelled");
  assert.equal(ev(s, "called").reason, "terminal_state");
  assert.equal(msgs(s, "called").length, 0);
  assert.deepEqual(s.tickets[Q.tkey(H, QU, TK)].anomalies, ["called_after_cancelled"]);
});
test("호출 문자 발송 전 취소가 오면 호출 문자를 무효화(정정 문자 불필요)", () => {
  const s = mk();
  ev(s, "called"); ev(s, "cancelled");
  assert.equal(msgs(s, "called")[0].state, "void");
  assert.equal(msgs(s, "correction").length, 0);
});
test("호출 문자 이미 발송 후 취소가 오면 정정 문자 1건", () => {
  const s = mk();
  ev(s, "called");
  Q.markResult(s, msgs(s, "called")[0].key, "sent", T);
  ev(s, "cancelled");
  assert.equal(msgs(s, "correction").length, 1);
  assert.match(msgs(s, "correction")[0].text, /정정/);
  assert.equal(snap(s).status, "cancelled");
});
test("호출 뒤 대기 인원 변경은 거부(숫자 되살아남 방지)", () => {
  const s = mk();
  ev(s, "called");
  assert.equal(ev(s, "queue_changed", { peopleAhead: 1 }).reason, "terminal_state");
  assert.equal(snap(s).ahead, null);
});
test("호출 전 근접 문자가 미발송이면 호출과 함께 무효화", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 }); ev(s, "called");
  assert.equal(msgs(s, "near")[0].state, "void");
});
test("발송 직전 재검증: 상태가 바뀐 근접 문자는 내보내지 않음", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 });
  ev(s, "paused");
  assert.equal(Q.deliverable(s, T).length, 0);
});
test("10분 지난 근접 문자는 발송하지 않음", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 });
  assert.equal(Q.deliverable(s, T + 700000).length, 0);
});

// ── 위험 5: 병원·대기열 혼선
test("같은 토큰이라도 다른 병원 이벤트는 내 접수에 적용되지 않음", () => {
  const s = mk();
  Q.register(s, { hospitalId: "hospB", queueId: QU, ticketToken: TK, label: "B-001", consent: false, baseSeq: 0 }, T);
  const r = Q.ingest(s, { eventId: "x1", sequence: 1, hospitalId: "hospB", queueId: QU, ticketToken: TK, type: "called", observedAt: T }, { now: T, authenticated: true });
  assert.equal(r.accepted, true);
  assert.equal(snap(s).status, "waiting"); // hospA 접수는 그대로
  assert.equal(Q.snapshot(s, "hospB", QU, TK, T).status, "called");
});
test("등록되지 않은 접수·대기열 이벤트는 새로 만들지 않고 거부", () => {
  const s = mk();
  assert.equal(ev(s, "called", {}, T, { override: { ticketToken: "ghost" } }).reason, "unknown_ticket");
  assert.equal(ev(s, "called", {}, T, { override: { queueId: "q9" } }).reason, "unknown_queue");
  assert.equal(Object.keys(s.tickets).length, 1);
});
test("대기열별 순서번호는 독립(다른 대기열 큰 번호가 영향 없음)", () => {
  const s = mk();
  Q.register(s, { hospitalId: H, queueId: "q2", ticketToken: "t9", label: "B-002", consent: false, baseSeq: 500 }, T);
  assert.equal(ev(s, "queue_changed", { peopleAhead: 2 }).accepted, true);
});
test("서명 검증되지 않은 출처는 모든 이벤트 거부", () => {
  const s = mk();
  assert.equal(ev(s, "called", {}, T, { auth: false }).reason, "unauthenticated");
  assert.equal(snap(s).status, "waiting");
});
test("이벤트 안의 verified:true 같은 자기주장 필드는 무시", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2, verified: true, estimate: { min: 5, max: 10 } }, T, { auth: false });
  assert.equal(snap(s).estimate, null);
});

// ── 위험 6: 예상 대기시간 오류
test("인증된 출처의 예상시간만, 인원과 일치할 때만 표시", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 3, estimate: { min: 10, max: 20 } });
  assert.deepEqual(snap(s).estimate, { min: 10, max: 20 });
  ev(s, "queue_changed", { peopleAhead: 2 }); // 새 이벤트에 예상 없음
  assert.equal(snap(s).estimate, null);
});
test("뒤집힌·음수·과대 예상시간은 숨김(인원은 유지)", () => {
  const s = mk();
  for (const est of [{ min: 30, max: 10 }, { min: -1, max: 5 }, { min: 5, max: 9999 }, { min: 1.5, max: 5 }]) {
    ev(s, "queue_changed", { peopleAhead: 2, estimate: est });
    assert.equal(snap(s).estimate, null); assert.equal(snap(s).ahead, 2);
  }
});
test("지연·일시정지 중엔 예상시간과 숫자 숨김", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 4, estimate: { min: 5, max: 9 } }); ev(s, "delayed");
  assert.equal(snap(s).estimate, null); assert.equal(snap(s).ahead, null);
  ev(s, "resumed"); // 재개 직후에는 기존 예상시간이 되살아나지 않아야 함
  assert.equal(snap(s).estimate, null);
});
test("재개 시 이미 3명 이하면 근접 문자를 한 번 평가", () => {
  const s = mk();
  ev(s, "paused"); ev(s, "queue_changed", { peopleAhead: 2 });
  assert.equal(msgs(s, "near").length, 0);
  ev(s, "resumed");
  assert.equal(msgs(s, "near").length, 1);
});

// ── 위험 7: 문자 미도착·오발송
test("발송 실패는 대기 후 재시도, 최대 횟수 후 '문자 문제' 표시", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 });
  const k = msgs(s, "near")[0].key;
  Q.markResult(s, k, "failed", T);
  assert.equal(Q.deliverable(s, T + 1000).length, 0); // 백오프 중
  assert.equal(Q.deliverable(s, T + 61000).length, 1);
  Q.markResult(s, k, "failed", T + 61000); Q.markResult(s, k, "failed", T + 200000);
  assert.equal(msgs(s, "near")[0].state, "failed_final");
  assert.equal(snap(s).textStatus, "problem");
  assert.equal(Q.deliverable(s, T + 500000).length, 0);
});
test("결과 '알 수 없음'은 자동 재발송하지 않음(이중 문자 방지)", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 });
  Q.markResult(s, msgs(s, "near")[0].key, "unknown", T);
  assert.equal(Q.deliverable(s, T + 100000).length, 0);
  assert.equal(snap(s).textStatus, "problem");
});
test("도착 확인된 문자는 상태를 되돌릴 수 없음", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2 });
  const k = msgs(s, "near")[0].key;
  Q.markResult(s, k, "delivered", T);
  assert.equal(Q.markResult(s, k, "failed", T), false);
  assert.equal(snap(s).textStatus, "delivered");
});
test("문자에는 수신자 참조만 있고 이름·진료과·진단 정보 없음, 수신자는 등록 시점 고정", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 2, department: "정형외과", patientName: "홍길동" });
  const d = Q.deliverable(s, T)[0];
  assert.equal(d.recipientRef, "r1");
  assert.doesNotMatch(d.text, /홍길동|정형외과|진단|주민|\d{3}-\d{4}-\d{4}/);
  assert.match(d.text, /병원 현장 호출이 우선/);
});
test("잘못된 입력(큰 수·비정수·문자열 순서·알 수 없는 타입)은 거부하고 상태 불변", () => {
  const s = mk();
  const before = JSON.stringify(s);
  for (const o of [{ peopleAhead: -1 }, { peopleAhead: 1.5 }, { peopleAhead: 99999 }, { peopleAhead: "3" }])
    assert.match(ev(s, "queue_changed", o).reason, /invalid:peopleAhead/);
  assert.match(ev(s, "queue_changed", { peopleAhead: 1 }, T, { override: { sequence: "5" } }).reason, /invalid:sequence/);
  assert.match(ev(s, "sendSMS").reason, /invalid:type/);
  assert.equal(JSON.stringify(s), before);
});
test("등록 전 안내: 숫자 없음·현장 호출 우선 문구", () => {
  const s = mk();
  assert.equal(snap(s).ahead, null); assert.match(snap(s).alert, /현장 호출이 우선/);
});

// ── 현재 호출 번호(참고 표시)
test("현재 호출 번호는 표시만 되고 대기 인원을 바꾸지 않음", () => {
  const s = mk();
  ev(s, "queue_changed", { peopleAhead: 4 });
  assert.equal(Q.setCurrentCall(s, H, QU, "A-020", T).ok, true);
  const v = snap(s);
  assert.equal(v.currentCall.label, "A-020"); assert.equal(v.ahead, 4);
});
test("현재 호출 번호: 잘못된 값·없는 대기열 거부, 오래되면 숨김", () => {
  const s = mk();
  assert.equal(Q.setCurrentCall(s, H, QU, "홍길동", T).reason, "invalid_label");
  assert.equal(Q.setCurrentCall(s, H, "nope", "A-1", T).reason, "unknown_queue");
  Q.setCurrentCall(s, H, QU, "A-020", T);
  assert.equal(snap(s, T + 700000).currentCall, null);
});
