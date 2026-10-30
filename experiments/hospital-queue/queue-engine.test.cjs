"use strict";
const test=require("node:test");
const assert=require("node:assert/strict");
const Q=require("./queue-engine.js");
const T=1000000;
function ev(state,id,type,extra={},time=T){
  return Q.next(state,{id,seq:state.lastSeq+1,type,...extra},time).state;
}
test("초기값은 모의 대기 6명, 발송 대기열 빈 값",()=>{
 const s=Q.initial(T);assert.equal(s.ahead,6);assert.equal(s.outbox.length,0);
});
test("대기 인원 변경 수신",()=>{
 const s=ev(Q.initial(T),"a","queue",{ahead:5});
 assert.equal(Q.snapshot(s,T).ahead,5);
});
test("3명 전 알림 문구 미리보기 생성",()=>{
 const s=ev(Q.initial(T),"a","queue",{ahead:3});
 assert.match(s.outbox[0],/모의 문자 · 미발송/);assert.match(s.outbox[0],/3명/);
});
test("임계값 이후 같은 알림을 중복 생성하지 않음",()=>{
 let s=ev(Q.initial(T),"a","queue",{ahead:3});s=ev(s,"b","queue",{ahead:2});
 assert.equal(s.outbox.length,1);
});
test("동일 이벤트 중복 수신 시 상태 및 문자 유지",()=>{
 let s=ev(Q.initial(T),"a","queue",{ahead:3});
 const result=Q.next(s,{id:"a",seq:2,type:"queue",ahead:1},T);
 assert.equal(result.accepted,false);assert.strictEqual(result.state,s);assert.equal(s.outbox.length,1);
});
test("과거 순서번호는 무시",()=>{
 let s=ev(Q.initial(T),"a","queue",{ahead:4});
 const res=Q.next(s,{id:"b",seq:1,type:"queue",ahead:1},T);
 assert.equal(res.accepted,false);assert.equal(res.state.ahead,4);
});
test("음수/비정수 대기 인원 거부",()=>{
 const s=Q.initial(T);
 assert.throws(()=>Q.next(s,{id:"a",seq:1,type:"queue",ahead:-1},T));
 assert.throws(()=>Q.next(s,{id:"a",seq:1,type:"queue",ahead:2.7},T));
});
test("근거 미확인 예상시간을 출력하지 않음",()=>{
 const s=ev(Q.initial(T),"a","estimate",{min:5,max:10,verified:false});
 assert.equal(Q.snapshot(s,T).estimate,null);
});
test("가상 병원 추정정보가 검증 표식을 가진 경우에만 시연",()=>{
 const s=ev(Q.initial(T),"a","estimate",{min:5,max:10,verified:true});
 assert.deepEqual(Q.snapshot(s,T).estimate,{min:5,max:10,verified:true});
});
test("뒤집힌 예상시간 범위는 숨김",()=>{
 const s=ev(Q.initial(T),"a","estimate",{min:30,max:10,verified:true});
 assert.equal(Q.snapshot(s,T).estimate,null);
});
test("2분 초과 갱신 실패는 대기/예상시간을 숨김",()=>{
 let s=ev(Q.initial(T),"a","estimate",{min:5,max:10,verified:true});
 assert.equal(Q.snapshot(s,T+120001).ahead,null);
 assert.equal(Q.snapshot(s,T+120001).estimate,null);
 assert.match(Q.snapshot(s,T+120001).alert,/갱신이 지연/);
});
test("일시중단 상태에는 추가 문자 없음",()=>{
 let s=ev(Q.initial(T),"a","pause");
 s=ev(s,"b","queue",{ahead:2});
 assert.equal(s.outbox.length,0);assert.equal(Q.snapshot(s,T).ahead,null);
});
test("대기 재개 후 정상 복귀",()=>{
 let s=ev(Q.initial(T),"a","pause");s=ev(s,"b","resume");
 assert.equal(Q.snapshot(s,T).status,"waiting");
});
test("호출 메시지는 모의 문구만 생성",()=>{
 const s=ev(Q.initial(T),"a","call");
 assert.equal(s.status,"called");assert.match(s.outbox[0],/미발송/);
});
test("취소 뒤에는 호출과 문자 방지",()=>{
 let s=ev(Q.initial(T),"a","cancel");
 const result=Q.next(s,{id:"b",seq:2,type:"call"},T);
 assert.equal(result.accepted,false);assert.equal(result.state.outbox.length,0);
});
test("호출 뒤에는 대기 정보 변경 불가",()=>{
 let s=ev(Q.initial(T),"a","call");
 const r=Q.next(s,{id:"b",seq:2,type:"queue",ahead:1},T);
 assert.equal(r.accepted,false);
});
test("민감정보 없이 접수번호만 표시",()=>{
 const s=ev(Q.initial(T),"a","queue",{ahead:3});
 assert.doesNotMatch(s.outbox[0],/환자명|주민등록|진단명|핸드폰번호/);
});
test("허용되지 않은 이벤트 거부",()=>{
 const s=Q.initial(T);assert.throws(()=>Q.next(s,{id:"a",seq:1,type:"sendSMS"},T));
});
