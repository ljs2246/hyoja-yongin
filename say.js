/* 버튼 옆 🔊: 누르면 그 버튼 내용만 읽어 줌(버튼 자체를 누르면 평소처럼 동작). 전화 버튼도 🔊는 전화를 걸지 않음. */
(function(){try{
if(!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance)return;
var path=location.pathname.split('/').pop()||'index.html',cur=null;
var D={'0':'공','1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구'};
function digits(s){return s.split('').map(function(c){return D[c];}).join(' ');}
function say(t){return t.replace(/\b119\b/g,'일일구').replace(/\b112\b/g,'일일이').replace(/\b129\b/g,'일이구')
  .replace(/\d[\d-]*\d|\d/g,function(m){return m.split('-').map(digits).join(', ');})
  .replace(/[›↗!]/g,' ').replace(/·/g,', ').replace(/\s+/g,' ').trim();}
function clean(a){return (a.textContent||'').replace(/\s+/g,' ').trim();}
function reset(){document.querySelectorAll('.hj-say2').forEach(function(b){b.setAttribute('aria-pressed','false');b.textContent='🔊';});cur=null;}
function speak(b,text){
  if(cur===b){try{speechSynthesis.cancel();}catch(x){}reset();return;}
  try{speechSynthesis.cancel();}catch(x){}reset();cur=b;b.setAttribute('aria-pressed','true');b.textContent='■';
  setTimeout(function(){var u=new SpeechSynthesisUtterance(text);u.lang='ko-KR';u.rate=0.9;
    var v=(speechSynthesis.getVoices()||[]).filter(function(x){return /^ko/i.test(x.lang);})[0];if(v)u.voice=v;
    u.onend=u.onerror=function(){if(cur===b)reset();};speechSynthesis.speak(u);},120);}
function mkBtn(label,text){var b=document.createElement('button');b.type='button';b.className='hj-say2';b.textContent='🔊';
  b.setAttribute('aria-pressed','false');b.setAttribute('aria-label',label+' 소리로 듣기');
  b.onclick=function(e){e.preventDefault();e.stopPropagation();speak(b,text);};return b;}
function wrapRow(a,btn){var w=document.createElement('div');w.className='hj-tw2';a.parentNode.insertBefore(w,a);w.appendChild(btn);w.appendChild(a);}
var css=document.createElement('style');
css.textContent='.hj-tw2{display:flex;align-items:center;gap:8px;width:100%}.hj-tw2>a{flex:1;min-width:0}'
+'.hj-say2{flex:0 0 56px;width:56px;height:56px;border-radius:50%;border:2px solid #D9A066;background:#fff;color:#7A3510;font-size:24px;line-height:1;padding:0;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 0 #E8C79B}'
+'.hj-say2[aria-pressed=true]{background:#7A3510;color:#fff;border-color:#7A3510}.hj-say2:focus-visible{outline:3px solid #A92B22;outline-offset:2px}'
+':is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair){flex-direction:column;align-items:stretch;gap:6px}:is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair) .hj-say2{flex:0 0 auto;width:100%;height:52px;border-radius:26px;font-size:20px}:is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair) .hj-say2::after{content:" 듣기";font-size:18px;font-weight:700}:is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair) .hj-say2[aria-pressed=true]::after{content:" 멈추기"}'
+'.hj-tw2.hj-pair{margin:6px 0}.hj-tw2.hj-pair .hj-say2{flex:0 0 auto;width:auto;height:52px;border-radius:26px;padding:0 16px;font-size:18px;font-weight:700;gap:6px}';
document.head.appendChild(css);
/* 홈: 급할 때 */
var urgent=document.querySelector('a.hj-urgent');
if(urgent){wrapRow(urgent,mkBtn('급할 때','급할 때. 일일구, 병원, 약국. 누르면 급할 때 화면으로 가요.'));}
/* 급할 때 화면: 전화 버튼 */
if(path==='Emergency.html'){
  document.querySelectorAll('main a[href^="tel:"],#main-content a[href^="tel:"]').forEach(function(a){
    if(a.closest('[data-hjnav]')||a.closest('.hj-tw2'))return;var t=clean(a);if(!t)return;
    wrapRow(a,mkBtn(t,say(t)+'. 누르면 바로 전화가 걸려요.'));});
  /* 약국·응급실 지도 찾기 버튼 묶음: 묶음마다 🔊 한 줄 */
  [['약국','가까운 약국을 지도에서 찾는 버튼이에요. 네이버 약국, 카카오 약국 중에서 고르세요.'],['응급실','가까운 응급실을 지도에서 찾는 버튼이에요. 네이버 응급실, 카카오 응급실 중에서 고르세요.']].forEach(function(k){
    var as=[].filter.call(document.querySelectorAll('a[target="_blank"]'),function(a){return clean(a).replace(/\s/g,'')===('네이버'+k[0])||clean(a).replace(/\s/g,'')===('카카오'+k[0]);});
    if(!as.length)return;var row=as[0].parentNode;if(!row||row.querySelector('.hj-say2'))return;
    var b=mkBtn(k[0]+' 찾기 지도 버튼',k[1]);b.textContent='🔊';var w=document.createElement('div');w.className='hj-tw2 hj-pair';row.parentNode.insertBefore(w,row);w.appendChild(b);
    var lab=document.createElement('span');lab.textContent=k[0]+' 찾기 버튼 듣기';lab.style.cssText='font-size:18px;font-weight:700;color:#6A4A33';w.appendChild(lab);});
}
window.addEventListener('pagehide',function(){try{speechSynthesis.cancel();}catch(x){}});
}catch(e){}})();
