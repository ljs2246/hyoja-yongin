const assert=require('node:assert/strict');
const profiles=require('../region-profiles.js');
const registry={has(code){return ['TEST_A','TEST_B'].includes(code);}};
function memory(initial){let value=initial||null;return {getItem(){return value;},setItem(k,v){value=v;}};}
let tests=0;function check(f){f();tests++;}
const storage=memory(),p=profiles.create(storage,registry);
p.select('mine','TEST_A');p.select('parents','TEST_B');p.activate('parents');
check(()=>assert.deepEqual(profiles.create(storage,registry).get(),{mine:'TEST_A',parents:'TEST_B',active:'parents',persistent:true}));
p.select('mine','TEST_B');
check(()=>assert.equal(p.get().parents,'TEST_B'));
p.clear('mine');
check(()=>assert.equal(p.get().parents,'TEST_B'));
check(()=>assert.equal(p.get().mine,null));
check(()=>assert.throws(()=>p.select('parents','UNKNOWN')));
check(()=>assert.throws(()=>p.select('invalid','TEST_A')));
const broken=profiles.create({getItem(){throw Error();},setItem(){throw Error();}},registry);
check(()=>assert.equal(broken.select('mine','TEST_A').persistent,false));
check(()=>assert.equal(broken.get().mine,'TEST_A'));
const removed=profiles.create(memory(JSON.stringify({version:1,mine:'DELETED_REGION',parents:'TEST_B'})),registry);
check(()=>assert.equal(removed.get().mine,null));
check(()=>assert.equal(removed.get().parents,'TEST_B'));
check(()=>assert.equal(profiles.create(memory('{broken'),registry).get().mine,null));
check(()=>assert.equal(profiles.create(memory(JSON.stringify({version:99,mine:'TEST_A'})),registry).get().mine,null));
console.log(tests+'개 내 지역·부모님 지역 저장·복원·오류 검사 통과');
