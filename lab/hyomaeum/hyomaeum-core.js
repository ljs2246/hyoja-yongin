/* 효마음 포인트 Phase 1 (격리 데모 · 11월 용인 시범 범위 밖 · 테스트 브랜치 전용)
   - 돈·현금·상품권·기부금·환급액이 아니며 교환·양도·환급이 없는 '마음' 표시 기능이에요.
   - 전화 내용·통화기록·문자함·위치·연락처를 읽지 않아요. 이용자가 직접 누른 기록만 이 휴대폰에 저장해요.
   - 앱이 실제 연락 여부를 확인하지 못해요(자기 기록). 완전한 부정 방지 불가 → 금전 가치 보상에는 절대 연결 금지. */
(function(root){
  var KEY='hj-hyomaeum-v1';
  var RULES={version:'r1',
    call:{points:50,period:'day'},msg:{points:20,period:'day'},visit:{points:100,period:'week'},
    weeklyBonus:{points:100,minDaysWithContact:5}}; // UI 시안용 가정값. 최종 규칙은 이용자 검증 후 사용자 승인
  var ACTIONS={call:'안부 전화',msg:'안부 메시지',visit:'직접 방문'};
  function kst(now){return new Date((now===undefined?Date.now():now)+9*3600*1000);}
  function kstDay(now){return kst(now).toISOString().slice(0,10);}
  function weekKey(now){ // 월요일 시작 ISO 주차(KST)
    var d=kst(now);var t=Date.UTC(d.getUTCFullYear(),d.getUTCMonth(),d.getUTCDate());var day=(new Date(t).getUTCDay()+6)%7;
    var thu=new Date(t+(3-day)*86400000);var y=thu.getUTCFullYear();var j1=Date.UTC(y,0,4);var wk=1+Math.round(((thu.getTime()-j1)/86400000-3+((new Date(j1).getUTCDay()+6)%7))/7);
    return y+'-W'+(wk<10?'0':'')+wk;}
  function rid(){var a=new Uint8Array(8);try{(root.crypto||require('crypto').webcrypto).getRandomValues(a);}catch(e){for(var i=0;i<8;i++)a[i]=Math.floor(Math.random()*256);}
    return Array.prototype.map.call(a,function(b){return(b<16?'0':'')+b.toString(16);}).join('');}
  function blank(){return {ver:1,enabled:false,anonymous_local_id:rid(),entries:[]};}
  function load(st){try{var s=JSON.parse(st.getItem(KEY)||'null');if(s&&s.ver===1&&Array.isArray(s.entries))return s;}catch(e){}return blank();}
  function save(st,s){try{st.setItem(KEY,JSON.stringify(s));return true;}catch(e){return false;}}
  function live(s){return s.entries.filter(function(e){return !e.deleted_at;});}
  function total(s){return live(s).reduce(function(a,e){return a+e.credited_points;},0);}
  function periodKey(action,now){return RULES[action].period==='week'?weekKey(now):kstDay(now);}
  function ikey(s,action,now){return s.anonymous_local_id+'|'+periodKey(action,now)+'|'+action+'|'+RULES.version;}
  function has(s,k){return s.entries.some(function(e){return e.idempotency_key===k;});} // 삭제한 기록도 키는 유지 → 지우고 다시 받기 방지
  function entry(s,action,now,pts,k){return {local_date:kstDay(now),action_type:action,reward_rule_version:RULES.version,credited_points:pts,idempotency_key:k,created_at:new Date(now).toISOString(),deleted_at:null};}
  function bonusDue(s,now){var wk=weekKey(now);var days={};
    live(s).forEach(function(e){if((e.action_type==='call'||e.action_type==='msg')&&e.week===wk)days[e.local_date]=1;});
    return Object.keys(days).length>=RULES.weeklyBonus.minDaysWithContact;}
  // 기록: 반환 {ok, reason, points, bonus, total}. 읽기→검사→쓰기를 한 번에 하고 저장 직전에 다시 읽어 확인
  function record(st,action,now){
    now=now===undefined?Date.now():now;
    if(!RULES[action]||action==='weeklyBonus')return {ok:false,reason:'unknown'};
    var s=load(st);if(!s.enabled)return {ok:false,reason:'disabled',total:total(s)};
    var k=ikey(s,action,now);if(has(s,k))return {ok:false,reason:'duplicate',total:total(s)};
    var s2=load(st);if(has(s2,k))return {ok:false,reason:'duplicate',total:total(s2)}; // 다른 창이 먼저 기록했는지 재확인
    s=s2;var e=entry(s,action,now,RULES[action].points,k);e.week=weekKey(now);s.entries.push(e);var bonus=0;
    var bk=s.anonymous_local_id+'|'+weekKey(now)+'|weeklyBonus|'+RULES.version;
    if(bonusDue(s,now)&&!has(s,bk)){var b=entry(s,'weeklyBonus',now,RULES.weeklyBonus.points,bk);b.week=weekKey(now);s.entries.push(b);bonus=b.credited_points;}
    if(!save(st,s))return {ok:false,reason:'storage_failed',total:total(load(st))}; // 조용히 바꾸지 않고 실패를 알림
    var chk=load(st);if(!has(chk,k))return {ok:false,reason:'storage_failed',total:total(chk)};
    return {ok:true,points:RULES[action].points,bonus:bonus,total:total(chk)};}
  function recordSafe(st,action,now){ // 여러 창 동시 클릭 대비: 브라우저 잠금이 있으면 사용
    if(root.navigator&&root.navigator.locks&&root.navigator.locks.request)return root.navigator.locks.request('hj-hyomaeum',function(){return record(st,action,now);});
    return Promise.resolve(record(st,action,now));}
  function setEnabled(st,on){var s=load(st);s.enabled=!!on;return save(st,s);}
  function deleteEntry(st,key,now){var s=load(st);var hit=false;s.entries.forEach(function(e){if(e.idempotency_key===key&&!e.deleted_at){e.deleted_at=new Date(now===undefined?Date.now():now).toISOString();hit=true;}});if(hit)save(st,s);return hit;}
  function deleteAll(st){try{st.removeItem(KEY);return st.getItem(KEY)===null;}catch(e){return false;}} // 전부 삭제(내부 식별자 포함)
  function summary(st,now){var s=load(st);var d=kstDay(now),w=weekKey(now);
    return {enabled:s.enabled,total:total(s),flowers:Math.floor(total(s)/100),
      today:{call:has(s,ikey(s,'call',now)),msg:has(s,ikey(s,'msg',now))},week:{visit:has(s,ikey(s,'visit',now))},
      count:live(s).filter(function(e){return e.action_type!=='weeklyBonus';}).length,day:d,weekKey:w};}
  var api={KEY:KEY,RULES:RULES,ACTIONS:ACTIONS,kstDay:kstDay,weekKey:weekKey,load:load,record:record,recordSafe:recordSafe,setEnabled:setEnabled,deleteEntry:deleteEntry,deleteAll:deleteAll,summary:summary,total:total};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.hjHyomaeum=api;
})(typeof window!=='undefined'?window:globalThis);
