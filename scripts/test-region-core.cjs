const assert=require('node:assert/strict');
const core=require('../region-core.js');
// Synthetic IDs and records only. Not official region or institution data.
const regions=core.registry([{code:'TEST_A'},{code:'TEST_A1',parentCode:'TEST_A'},{code:'TEST_A2',parentCode:'TEST_A'},{code:'TEST_B'},{code:'TEST_B1',parentCode:'TEST_B'}]);
const base={institutionId:'TEST_INST_1',sourceId:'TEST_SOURCE',sourceRecordId:'TEST_RECORD_1',name:'가상 기관',address:'시험 주소 1',regionCode:'TEST_A1',addressRegionCode:'TEST_A1',kind:'pharmacy',locationVerified:true,kindVerified:true,sourceUrl:'https://example.invalid/test',verifiedAt:'2026-10-26'};
let checks=0;
function check(fn){fn();checks++;}
check(()=>assert.equal(core.selectInstitutions([base],'TEST_A1','pharmacy',regions).items.length,1));
check(()=>assert.equal(core.selectInstitutions([base],'TEST_A','pharmacy',regions).items.length,1));
check(()=>assert.equal(core.selectInstitutions([base],'TEST_A2','pharmacy',regions).items.length,0));
check(()=>assert.equal(core.selectInstitutions([base],'TEST_B1','pharmacy',regions).items.length,0));
check(()=>assert.equal(core.selectInstitutions([base],'TEST_A1','hospital',regions).items.length,0));
for(const mutation of [{addressRegionCode:'TEST_B1'},{locationVerified:false},{kindVerified:false},{verifiedAt:''},{sourceRecordId:''},{sourceUrl:''}])
 check(()=>assert.equal(core.selectInstitutions([{...base,...mutation}],'TEST_A1','pharmacy',regions).withheld.length,1));
check(()=>assert.equal(core.selectInstitutions([base,{...base,institutionId:'TEST_INST_2',sourceRecordId:'TEST_RECORD_2'}],'TEST_A1','pharmacy',regions).items.length,0));
check(()=>assert.equal(core.selectInstitutions([base,{...base,address:'다른 주소'}],'TEST_A1','pharmacy',regions).items.length,0));
check(()=>assert.ok(core.selectInstitutions([base],'UNKNOWN','pharmacy',regions).error));
check(()=>assert.equal(core.appliesToRegion({scope:'regional',regionCode:'TEST_A',scopeVerified:true},'TEST_A1',regions),true));
check(()=>assert.equal(core.appliesToRegion({scope:'regional',regionCode:'TEST_A1',scopeVerified:true},'TEST_A2',regions),false));
check(()=>assert.equal(core.appliesToRegion({scope:'national',scopeVerified:false},'TEST_A1',regions),false));
const session=core.selectionSession();session.change('TEST_A1');const old=session.begin();session.change('TEST_B1');const current=session.begin();
check(()=>assert.equal(session.accepts(old),false));
check(()=>assert.equal(session.accepts(current),true));
const newer=session.begin();
check(()=>assert.equal(session.accepts(current),false));
check(()=>assert.equal(session.accepts(newer),true));
session.change('TEST_A1');
check(()=>assert.equal(session.accepts(old),false));
check(()=>assert.throws(()=>core.registry([{code:'A',parentCode:'B'},{code:'B',parentCode:'A'}])));
check(()=>assert.throws(()=>core.registry([{code:'A',parentCode:'MISSING'}])));
console.log(checks+'개 전국 지역 격리·분류·중복·적용 범위·응답 역전 검사 통과');
