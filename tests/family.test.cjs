const f=require('../family.js');let ok=0,bad=0;
function t(n,v){if(v){ok++;}else{bad++;console.log('FAIL',n);}}
t('휴대폰 정상',f.validPhone('010-1234-5678'));t('짧은 번호 거부',!f.validPhone('010-12-34'));t('글자 거부',!f.validPhone('abc'));
t('지역번호 031',f.validPhone('031-328-0325'));t('서울 02',f.validPhone('02-123-4567'));
t('서식',f.fmt('01012345678')==='010-1234-5678');
t('sms 링크',f.smsHref('010-1234-5678','안녕 ').startsWith('sms:01012345678?&body=%EC%95%88'));
t('KST 날짜',f.kstDay(Date.UTC(2026,9,30,16,0,0))==='2026-10-31'&&f.kstDay(Date.UTC(2026,9,30,14,59,0))==='2026-10-30');
const mem=(()=>{let m={};return{getItem:k=>k in m?m[k]:null,setItem:(k,v)=>{m[k]=String(v)}}})();
t('빈 로드',f.load(mem).length===0);f.save(mem,[{name:'큰딸',phone:'01012345678'},{name:'x',phone:'123'}]);t('잘못된 번호 걸러냄',f.load(mem).length===1);
f.save(mem,[1,2,3,4].map(i=>({name:'a'+i,phone:'0101234567'+i})));t('최대 3명',f.load(mem).length===3);
const now=Date.UTC(2026,9,30,0,0,0);f.setCheck(mem,now);t('오늘 안부 기록',!!f.getCheck(mem,now));t('다음 날엔 초기화',f.getCheck(mem,now+24*3600*1000)===null);
console.log('통과',ok,'실패',bad);process.exit(bad?1:0);
