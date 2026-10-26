const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
let checked=0;const errors=[];
for(const file of fs.readdirSync(root).filter(n=>n.endsWith('.html'))){
 const html=fs.readFileSync(path.join(root,file),'utf8');
 for(const m of html.matchAll(/<a\b[^>]*href="tel:([^"]+)"[^>]*>([\s\S]*?)<\/a>/g)){
  const text=m[2].replace(/<[^>]+>/g,' ');
  const displayed=text.match(/\b(?:0\d{1,3}-\d{3,4}-\d{4}|1\d{3}-\d{4}|1\d{2})\b/);
  if(!displayed)continue;
  checked++;
  if(displayed[0].replace(/\D/g,'')!==m[1].replace(/\D/g,''))errors.push(file+': '+displayed[0]+' != '+m[1]);
 }
}
if(errors.length){console.error(errors.join('\n'));process.exit(1);}
console.log(checked+'개 정적 전화 링크의 표시 번호·연결 값 일치 확인. 실제 통화·번호 최신성은 별도 검증 필요.');
