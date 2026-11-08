/* 효자 병원 대기 알림 로컬 시뮬레이터 (실제 병원/문자 API 미연결) */
(function(root,factory){
  const api=factory();
  if(typeof module!=="undefined"&&module.exports) module.exports=api;
  else root.HyojaQueueDemo=api;
})(typeof globalThis!=="undefined"?globalThis:this,function(){
  "use strict";
  const MAX_AGE_MS=120000;
  function initial(now=Date.now()){
    return {ticket:"A-023",ahead:6,status:"waiting",updatedAt:now,lastSeq:0,
      seenIds:[],notifiedClose:false,outbox:[],estimate:null};
  }
  function next(s,e,now=Date.now()){
    if(!s||!e||typeof e.id!=="string"||!e.id||!Number.isSafeInteger(e.seq)||e.seq<1)
      throw new Error("잘못된 병원 이벤트");
    if(s.seenIds.includes(e.id)||e.seq<=s.lastSeq) return {state:s,accepted:false,reason:"중복 또는 과거 이벤트"};
    if(!["queue","estimate","pause","resume","call","cancel"].includes(e.type))
      throw new Error("허용되지 않은 이벤트");
    if(["called","cancelled"].includes(s.status))
      return {state:s,accepted:false,reason:"종료된 접수"};
    const t={...s,seenIds:[...s.seenIds,e.id],outbox:[...s.outbox],lastSeq:e.seq,updatedAt:now};
    if(e.type==="queue"){
      if(!Number.isInteger(e.ahead)||e.ahead<0||e.ahead>999) throw new Error("잘못된 대기 인원");
      t.ahead=e.ahead;
      // 진료 지연 상황에서는 호출 알림을 만들지 않음
      if(t.status==="waiting"&&e.ahead<=3&&!t.notifiedClose){
        t.notifiedClose=true;
        t.outbox.push("[모의 문자 · 미발송] 접수번호 "+s.ticket+" · 앞에 "+e.ahead+"명 남았습니다. 병원 현장 호출을 우선 확인해 주세요.");
      }
    } else if(e.type==="estimate"){
      // 병원의 승인된 계산 결과로 검증된 경우에만 노출 가능. 이 데모 자체는 모두 가상 데이터.
      if(e.verified===true&&Number.isInteger(e.min)&&Number.isInteger(e.max)&&e.min>=0&&e.max>=e.min&&e.max<=240)
        t.estimate={min:e.min,max:e.max,verified:true};
      else t.estimate=null;
    } else if(e.type==="pause"){
      t.status="paused"; t.estimate=null;
    } else if(e.type==="resume"){
      t.status="waiting";
    } else if(e.type==="call"){
      t.status="called";t.estimate=null;
      t.outbox.push("[모의 문자 · 미발송] 접수번호 "+s.ticket+" · 병원에서 호출했습니다. 현장 직원 안내를 확인해 주세요.");
    } else if(e.type==="cancel"){
      t.status="cancelled";t.estimate=null;
    }
    return {state:t,accepted:true,reason:"모의 이벤트 적용"};
  }
  function snapshot(s,now=Date.now()){
    const fresh=(now>=s.updatedAt)&&(now-s.updatedAt<=MAX_AGE_MS);
    const waiting=s.status==="waiting";
    return {ticket:s.ticket,status:s.status,fresh,
      ahead:fresh&&waiting?s.ahead:null,
      estimate:fresh&&waiting&&s.estimate&&s.estimate.verified?{...s.estimate}:null,
      updatedAt:s.updatedAt,
      alert:!fresh?"병원 정보 갱신이 지연됐습니다. 실제 차례는 병원 현장 안내를 확인해 주세요.":
        s.status==="paused"?"병원 대기 안내가 일시중단됐습니다. 현장 안내를 확인해 주세요.":
        s.status==="called"?"호출되었습니다. 현장 안내를 확인해 주세요.":
        s.status==="cancelled"?"접수가 취소됐습니다.":"진료 순서가 바뀔 수 있습니다. 현장 호출을 우선 확인해 주세요.",
      outbox:[...s.outbox]};
  }
  return {initial,next,snapshot,MAX_AGE_MS};
});
