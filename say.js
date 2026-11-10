/* 버튼 옆 🔊: 누르면 그 버튼 내용만 읽어 줌(버튼 자체를 누르면 평소처럼 동작). 전화 버튼도 🔊는 전화를 걸지 않음. */
(function(){try{
var OK=('speechSynthesis' in window)&&!!window.SpeechSynthesisUtterance;
/* 앱 안 화면 등 소리 기능이 없는 곳에서도 🔊는 보이고, 누르면 이유와 해결 방법을 알려 줌 */
window.__hjSayNotice=function(){var n=document.getElementById('hj-say-notice');if(!n){n=document.createElement('div');n.id='hj-say-notice';n.setAttribute('role','status');n.style.cssText='position:fixed;left:12px;right:12px;bottom:calc(88px + env(safe-area-inset-bottom,0px));z-index:99999;background:#3B2A20;color:#fff;padding:14px 16px;border-radius:14px;font-size:17px;line-height:1.5;box-shadow:0 4px 16px rgba(0,0,0,.3)';n.textContent='지금 열린 화면(앱 안 화면)에서는 소리 읽기를 쓸 수 없어요. 오른쪽 위 ⋮ 메뉴에서 「다른 브라우저로 열기」를 눌러 크롬이나 삼성 인터넷으로 열어 주세요.';document.body.appendChild(n);}n.hidden=false;clearTimeout(n._t);n._t=setTimeout(function(){n.hidden=true;},7000);};
var path=location.pathname.split('/').pop()||'index.html',cur=null;
var D={'0':'공','1':'일','2':'이','3':'삼','4':'사','5':'오','6':'육','7':'칠','8':'팔','9':'구'};
function digits(s){return s.split('').map(function(c){return D[c];}).join(' ');}
function say(t){t=t.replace(/([가-힣A-Za-z)])(\d)/g,'$1 $2');
  return t.replace(/\b119\b/g,'일일구').replace(/\b112\b/g,'일일이').replace(/\b129\b/g,'일이구')
  .replace(/\d{2,4}-\d{3,4}-\d{4}|\d{4}-\d{4}|\d{7,}|\b1\d{2,3}\b(?![\d월일년명원개번회시분세%])/g,function(m){return m.split('-').map(digits).join(', ');})
  .replace(/[›↗!]/g,' ').replace(/·/g,', ').replace(/\s+/g,' ').trim();}
function clean(a){return (a.textContent||'').replace(/\s+/g,' ').trim();}
function reset(){document.querySelectorAll('.hj-say2').forEach(function(b){b.setAttribute('aria-pressed','false');b.textContent='🔊';});cur=null;}
function speak(b,text){
  if(!OK){window.__hjSayNotice();return;}
  if(cur===b){try{speechSynthesis.cancel();}catch(x){}reset();return;}
  try{speechSynthesis.cancel();}catch(x){}reset();cur=b;b.setAttribute('aria-pressed','true');b.textContent='■';
  setTimeout(function(){var u=new SpeechSynthesisUtterance(text);u.lang='ko-KR';u.rate=0.9;
    var v=(speechSynthesis.getVoices()||[]).filter(function(x){return /^ko/i.test(x.lang);})[0];if(v)u.voice=v;
    u.onend=u.onerror=function(){if(cur===b)reset();};speechSynthesis.speak(u);},120);}
function mkBtn(label,text){var b=document.createElement('button');b.type='button';b.className='hj-say2';b.textContent='🔊';
  b.setAttribute('aria-pressed','false');b.setAttribute('aria-label',label+' 소리로 듣기');
  b.onclick=function(e){e.preventDefault();e.stopPropagation();speak(b,text);};return b;}
function wrapRow(a,btn,after){var w=document.createElement('div');w.className='hj-tw2';try{var pp=a.parentNode,pd=pp&&getComputedStyle(pp);if(pd&&(pd.display==='grid'||(pd.display==='flex'&&pd.flexDirection.indexOf('row')===0)||pd.display==='inline-flex'))w.className='hj-tw2 hj-col';}catch(x){}a.parentNode.insertBefore(w,a);if(after){w.className='hj-tw2 hj-col hj-after';w.appendChild(a);w.appendChild(btn);}else{w.appendChild(btn);w.appendChild(a);}}
var css=document.createElement('style');
css.textContent='.hj-tw2{display:flex;align-items:center;gap:8px;width:100%}.hj-tw2>a{flex:1;min-width:0}'
+'.hj-say2{flex:0 0 auto;width:auto;min-width:96px;height:56px;border-radius:28px;padding:0 14px;gap:4px;border:2px solid #D9A066;background:#fff;color:#7A3510;font-size:24px;line-height:1;cursor:pointer;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 0 #E8C79B}'
+'.hj-say2::after{content:" 듣기";font-size:18px;font-weight:700}.hj-say2[aria-pressed=true]::after{content:" 멈추기"}'
+'.hj-say2[aria-pressed=true]{background:#7A3510;color:#fff;border-color:#7A3510}.hj-say2:focus-visible{outline:3px solid #A92B22;outline-offset:2px}'
+':is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair){flex-direction:column;align-items:stretch;gap:6px}:is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair) .hj-say2{flex:0 0 auto;width:100%;height:52px;border-radius:26px;font-size:20px}:is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair) .hj-say2::after{content:" 듣기";font-size:18px;font-weight:700}:is(.hj-narrow,.home-narrow) .hj-tw2:not(.hj-pair) .hj-say2[aria-pressed=true]::after{content:" 멈추기"}'
+'.hj-tw2.hj-col{flex-direction:column;align-items:stretch;gap:6px;min-width:0}.hj-tw2.hj-col .hj-say2{flex:0 0 auto;width:100%;min-width:0;padding:0 4px;height:52px;border-radius:26px;font-size:20px}'
+'.hj-tw2.hj-after .hj-say2{height:48px;font-size:20px}.hj-tw2.hj-after{gap:6px;margin-bottom:6px}'
+'.hj-tw2.hj-pair{margin:6px 0}.hj-tw2.hj-pair .hj-say2{flex:0 0 auto;width:auto;height:52px;border-radius:26px;padding:0 16px;font-size:18px;font-weight:700;gap:6px}';
document.head.appendChild(css);
/* 홈: 급할 때 */
var urgent=document.querySelector('a.hj-urgent');
if(urgent){wrapRow(urgent,mkBtn('급할 때','급할 때. 일일구, 병원, 약국. 누르면 급할 때 화면으로 가요.'));}
/* 급할 때 화면: 전화 버튼 */
if(path==='Emergency.html'){
  document.querySelectorAll('main a[href^="tel:"],#main-content a[href^="tel:"]').forEach(function(a){
    if(a.closest('[data-hjnav]')||a.closest('.hj-tw2'))return;var t=clean(a);if(!t)return;
    wrapRow(a,mkBtn(t,say(t)+'. 누르면 바로 전화가 걸려요.'),true);});
  /* 약국·응급실 지도 찾기 버튼 묶음: 묶음마다 🔊 한 줄 */
  [['약국','가까운 약국을 지도에서 찾는 버튼이에요. 네이버 약국, 카카오 약국 중에서 고르세요.'],['응급실','가까운 응급실을 지도에서 찾는 버튼이에요. 네이버 응급실, 카카오 응급실 중에서 고르세요.']].forEach(function(k){
    var as=[].filter.call(document.querySelectorAll('a[target="_blank"]'),function(a){return clean(a).replace(/\s/g,'')===('네이버'+k[0])||clean(a).replace(/\s/g,'')===('카카오'+k[0]);});
    if(!as.length)return;var row=as[0].parentNode;if(!row)return;row.setAttribute('data-hjmap','1');if(document.querySelector('.hj-pair[data-hjk="'+k[0]+'"]'))return;
    var b=mkBtn(k[0]+' 찾기 지도 버튼',k[1]);b.textContent='🔊';var w=document.createElement('div');w.className='hj-tw2 hj-pair';w.setAttribute('data-hjk',k[0]);row.parentNode.insertBefore(w,row);w.appendChild(b);
    var lab=document.createElement('span');lab.textContent=k[0]+' 찾기 버튼 듣기';lab.style.cssText='font-size:18px;font-weight:700;color:#6A4A33';w.appendChild(lab);});
}

/* 모든 화면: 눌러서 이동·전화·열기 하는 버튼마다 🔊 한 개. 🔊는 전화를 걸거나 화면을 옮기지 않고 읽어 주기만 함. */
if(path!=='Review.html'){
  var SKIP='[data-hjnav],[data-hjfoot],#hj-readbar,#hj-sizebar,#hj-sndbar,#sizeBtns,#hj-share-x,#hj-kakao,footer,header,.hj-tw,.hj-tw2,.hj-say2,.hj-say,.home-nav,details.home-sound-settings,form,[role=tablist]';
  var busy=false;
  function pass(){
    if(busy)return;busy=true;
    try{[].slice.call(document.querySelectorAll('a[href],button')).forEach(function(a){try{
      if(a.closest(SKIP)||a.classList.contains('hj-say2')||a.disabled)return;if(a.parentNode&&a.parentNode.getAttribute&&a.parentNode.getAttribute('data-hjmap'))return;
      var h=a.getAttribute('href')||'';
      if(a.tagName==='A'&&(h.charAt(0)==='#'||h==='index.html'||h===''))return;
      if(getComputedStyle(a).display==='none')return;
      var t=clean(a);if(!t)return;
      var tail=a.tagName==='BUTTON'?' 버튼이에요.':/^tel:/.test(h)?'. 누르면 바로 전화가 걸려요.':/^https?:/.test(h)?'. 누르면 안내 화면이 열려요.':'. 누르면 그 화면으로 가요.';
      wrapRow(a,mkBtn(t.slice(0,40),say(t)+tail));}catch(e){window.__sayErr=(window.__sayErr||0)+1;}});}catch(x){}
    fit();busy=false;}
  /* 글자를 크게 하면 한 줄에 안 들어가는 칸은 🔊를 위/아래로 옮겨요 */
  function fit(){try{[].slice.call(document.querySelectorAll('.hj-tw2:not(.hj-col):not(.hj-pair)')).forEach(function(w){
    var a=w.querySelector('a,button:not(.hj-say2)');if(!a)return;
    if(w.scrollWidth>w.clientWidth+1||a.scrollWidth>a.clientWidth+1||w.getBoundingClientRect().right>document.documentElement.clientWidth+1)w.classList.add('hj-col');});}catch(x){}}
  window.addEventListener('resize',function(){fit();});
  pass();
  /* 검색 결과처럼 나중에 생기는 버튼에도 🔊를 붙여요 (0.3초에 한 번만 확인, 내가 만든 변화는 무시) */
  try{var tm=null,obs=new MutationObserver(function(){if(tm)return;tm=setTimeout(function(){tm=null;pass();try{obs.takeRecords();}catch(x){}},300);});
    obs.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['class','style','hidden','open']});obs.observe(document.documentElement,{attributes:true,attributeFilter:['class','style']});}catch(x){}
}
window.addEventListener('pagehide',function(){try{if(OK)speechSynthesis.cancel();}catch(x){}});
}catch(e){}})();
