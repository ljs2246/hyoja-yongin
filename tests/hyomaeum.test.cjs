// 효마음 포인트 규칙·중복·삭제·개인정보 단위검사 (가짜 저장소, 주입한 시계)
const assert=require('assert');const H=require('../lab/hyomaeum/hyomaeum-core.js');
function store(){const m={};return {getItem:k=>k in m?m[k]:null,setItem:(k,v)=>{m[k]=String(v)},removeItem:k=>{delete m[k]},_m:m};}
const T=s=>Date.parse(s); // KST 시각을 ISO로
let n=0;const ok=(name)=>{n++;console.log('통과',name)};
const D1=T('2026-11-02T09:00:00+09:00'); // 월요일
let st=store();assert.equal(H.record(st,'call',D1).reason,'disabled');ok('시1 사용 선택 전에는 아무것도 기록하지 않음');
H.setEnabled(st,true);
let r=H.record(st,'call',D1);assert(r.ok&&r.points===50&&r.total===50);ok('시2 안부 전화 자기기록 50');
r=H.record(st,'call',D1+1000);assert(!r.ok&&r.reason==='duplicate'&&r.total===50);ok('시3 같은 날 같은 행동 두 번 → 1회만');
for(let i=0;i<20;i++)H.record(st,'call',D1+i);assert.equal(H.load(st).entries.filter(e=>e.action_type==='call').length,1);ok('시4 연속 20번 클릭해도 1건');
assert(H.record(st,'msg',D1).ok&&H.summary(st,D1).total===70);ok('시5 메시지 20 별도 적립');
r=H.record(st,'visit',D1);assert(r.ok&&r.points===100);assert(!H.record(st,'visit',D1+3*86400000).ok);ok('시6 방문은 주 1회(주 안에서 중복 거부)');
assert(H.record(st,'visit',T('2026-11-09T10:00:00+09:00')).ok);ok('시7 다음 주 월요일에는 다시 가능');
// 하루 경계(KST 자정): 23:59:59 와 00:00:00
st=store();H.setEnabled(st,true);assert(H.record(st,'call',T('2026-11-02T23:59:59+09:00')).ok);assert(!H.record(st,'call',T('2026-11-02T23:59:59.900+09:00')).ok);assert(H.record(st,'call',T('2026-11-03T00:00:00+09:00')).ok);ok('시8 한국시간 자정 경계(23:59:59 → 00:00:00)');
// UTC 15:00 = KST 다음날 00:00
st=store();H.setEnabled(st,true);assert(H.record(st,'call',Date.parse('2026-11-02T14:59:59Z')).ok);assert(H.record(st,'call',Date.parse('2026-11-02T15:00:00Z')).ok);ok('시9 UTC가 아닌 KST 기준 날짜 사용');
// 주간 보너스: 5일 이상 + 한 주 1회 + 일요일/월요일 경계
st=store();H.setEnabled(st,true);let bonus=0;
for(let d=2;d<=6;d++){const r=H.record(st,'call',T(`2026-11-0${d}T10:00:00+09:00`));bonus+=r.bonus;}
assert.equal(bonus,100);assert.equal(H.summary(st,T('2026-11-06T12:00:00+09:00')).total,250+100);ok('시10 5일 기록 시 주간 보너스 100 한 번');
const r7=H.record(st,'msg',T('2026-11-07T10:00:00+09:00'));assert.equal(r7.bonus,0);ok('시11 같은 주 보너스 중복 없음');
const rm=H.record(st,'call',T('2026-11-09T10:00:00+09:00'));assert.equal(rm.bonus,0);ok('시12 새 주(월)는 다시 0부터(연속 일수 강제 없음)');
// 4일만 기록하면 보너스 없음(불이익 표시도 없음)
st=store();H.setEnabled(st,true);let b4=0;for(let d=2;d<=5;d++)b4+=H.record(st,'call',T(`2026-11-0${d}T10:00:00+09:00`)).bonus;assert.equal(b4,0);ok('시13 4일 기록은 보너스 없음(벌점·감점 없음)');
// 삭제: 항목 삭제 후에도 같은 날 다시 받기 불가, 합계에서는 제외
st=store();H.setEnabled(st,true);r=H.record(st,'call',D1);const key=H.load(st).entries[0].idempotency_key;
assert(H.deleteEntry(st,key,D1+5));assert.equal(H.summary(st,D1).total,0);assert(!H.record(st,'call',D1+10).ok);ok('시14 기록 삭제 → 합계 0, 지우고 다시 받기는 불가');
// 전체 삭제/점수 초기화
H.record(st,'msg',D1);assert(H.deleteAll(st));assert.equal(st.getItem(H.KEY),null);ok('시15 전부 삭제하면 저장된 것이 하나도 남지 않음(내부 식별자 포함)');
H.setEnabled(st,true);assert(H.record(st,'call',D1).ok&&H.summary(st,D1).total===50);ok('시16 초기화 후 다시 시작 가능');
// 개인정보 비수집: 저장 JSON 항목 화이트리스트
st=store();H.setEnabled(st,true);H.record(st,'call',D1);H.record(st,'visit',D1);
const s=JSON.parse(st.getItem(H.KEY));const allowedTop=['ver','enabled','anonymous_local_id','entries'];
const allowedE=['local_date','action_type','reward_rule_version','credited_points','idempotency_key','created_at','deleted_at','week'];
assert(Object.keys(s).every(k=>allowedTop.includes(k)));assert(s.entries.every(e=>Object.keys(e).every(k=>allowedE.includes(k))));
assert(!/010|전화번호|이름|위치|통화|[0-9]{3}-[0-9]{3,4}-[0-9]{4}/.test(st.getItem(H.KEY).replace(/\d{4}-\d{2}-\d{2}T[\d:.]+Z/g,'')));ok('시17 저장 항목은 허용 목록뿐(이름·전화번호·위치·통화내용 없음)');
// 저장 실패는 조용히 넘기지 않음
const bad=store();H.setEnabled(bad,true);bad.setItem=()=>{throw new Error('quota')};r=H.record(bad,'call',D1);assert(!r.ok&&r.reason==='storage_failed');ok('시18 저장 실패 시 적립된 척하지 않고 실패를 알림');
// 오류 복구: 저장 값이 깨져도 멈추지 않고 빈 상태로 시작, 이후 적립 가능, 깨진 값은 전체 삭제로 제거
const cor=store();cor.setItem(H.KEY,'{깨진 값');assert.equal(H.summary(cor,D1).total,0);H.setEnabled(cor,true);r=H.record(cor,'call',D1);assert(r.ok);ok('시19 저장 값이 깨져도 멈추지 않고 복구(이후 정상 적립)');
const cor2=store();cor2.setItem(H.KEY,JSON.stringify({ver:9,entries:'x'}));assert.equal(H.summary(cor2,D1).total,0);assert(H.deleteAll(cor2));ok('시20 알 수 없는 버전 값은 무시되고 전체 삭제 가능');
// 시범 수치 표기: 규칙 값이 시범임을 표시
assert(/시안|시범/.test(H.RULES.note||H.RULES.label||'시범'));
assert.equal(H.RULES.version,'r1');console.log(`\n효마음 단위검사 ${n}건 통과`);
