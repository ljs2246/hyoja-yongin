(function(){
  var kids=document.body.children,wrap=null;
  for(var i=0;i<kids.length;i++){if(kids[i].tagName==='DIV'){wrap=kids[i];break;}}
  if(!wrap)return;
  var f=document.createElement('div');f.setAttribute('data-hjfoot','1');
  f.style.cssText='margin:8px 20px 20px;padding:14px 16px;border-top:2px solid #F0D6B5;font-family:inherit;color:#6A4A33;font-size:16px;line-height:1.6;word-break:keep-all';
  var a=document.createElement('div');a.textContent='「효자 용인」은 개인이 만든 안내 사이트예요. 용인시를 비롯한 어떤 공공기관과도 관계가 없어요.';
  var b=document.createElement('div');b.textContent='공식 자료의 출처와 확인한 날짜를 함께 적었어요. 가시기 전에 꼭 한 번 더 확인해 주세요.';
  var c=document.createElement('div');c.style.cssText='margin-top:6px;font-weight:700;color:#3B2314';
  var u=['hyoja.yongin','gmail.com'].join('@');
  c.appendChild(document.createTextNode('운영: 효자 용인 운영팀 · 문의: '));
  var m=document.createElement('a');m.href='mailto:'+u;m.textContent=u;m.style.cssText='color:#B8501A;text-decoration:underline;overflow-wrap:anywhere';
  c.appendChild(m);
  var fb=document.createElement('a');fb.href='mailto:'+u+'?subject='+encodeURIComponent('효자 용인 의견');fb.textContent='의견 보내기';
  fb.style.cssText='display:flex;align-items:center;justify-content:center;margin-top:10px;min-height:48px;border-radius:24px;border:2px solid #D9A066;background:#fff;color:#B8501A;font-size:18px;font-weight:700;text-decoration:none';
  f.appendChild(a);f.appendChild(b);f.appendChild(c);f.appendChild(fb);
  var nav=wrap.querySelector('div[data-hjnav],div[style*="repeat(6"]');
  if(nav&&nav.parentNode)nav.parentNode.insertBefore(f,nav);else wrap.appendChild(f);


  // 실제 제공 기능인 일반 공유 또는 주소 복사를 안내해요.
  try{var old=document.getElementById('hj-share');
    if(old&&!document.getElementById('hj-kakao')){
      var k=document.createElement('button');k.type='button';k.id='hj-kakao';
      k.textContent='가족에게 공유·주소 복사';
      k.style.cssText='min-height:64px;width:100%;border:0;border-radius:32px;background:#FEE500;color:#3A1D1D;box-shadow:0 5px 0 #D9C300;font-family:inherit;font-size:20px;font-weight:900;cursor:pointer';
      k.onclick=function(){old.click();};
      old.parentNode.insertBefore(k,old);old.style.display='none';
    }}catch(e){}
  // 인터넷이 느리거나 끊겨도 저장된 화면을 보여 줘요
  try{if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js');}catch(e){}
})();

// ── 익명 이용 통계 (기본 꺼짐) ──────────────────────────────────────────
// 원칙: 쿠키·저장 없음 / 검색어·전화번호·위치·건강정보 전송 금지 / 아래 허용 형식의 이름만 보냄.
// 켜는 방법: 대표 승인 후 효자 전용 GoatCounter 사이트 코드를 GC에 넣기. 비어 있으면 아무것도 보내지 않아요.
// 외부 스크립트는 불러오지 않고, 작은 이미지 요청(tracking pixel) 하나로만 보냅니다.
(function(){
  var GC='';
  var local=/^(localhost|127\.0\.0\.1)$/.test(location.hostname);
  var T=local?window.__HJ_STATS_TEST:null;            // 시험용 설정은 내 컴퓨터(localhost)에서만 인정
  var code=(T&&T.code)||GC, sink=T&&T.sink;
  if(!code&&!sink)return;
  try{if(navigator.doNotTrack==='1'||window.doNotTrack==='1'||navigator.globalPrivacyControl)return;}catch(e){}
  if(local&&!(T&&T.allowLocal))return;                // 개발 중 방문은 세지 않음
  var OK=/^(search-(pharmacy|emergency)-(all|chein|giheung|suji)-q[01]|tel-[a-z]{2,12}|map-(pharmacy|emergency)|gu-(chein|giheung|suji)|size-(normal|large|xl))$/;
  var PATH=/^\/[A-Za-z0-9_.\-]*$/;
  var GU={'':'all','처인구':'chein','기흥구':'giheung','수지구':'suji'};
  function bucket(){var w=window.innerWidth||0,b=[320,360,390,430,600,768,1024,1440],r=0;for(var i=0;i<b.length;i++){if(w>=b[i])r=b[i];}return r;}
  function send(p,isEvent){
    if(sink){try{sink.push({name:p,event:!!isEvent});}catch(e){}}
    if(!code||!/^[a-z0-9-]{1,40}$/.test(code))return;
    try{var im=new Image();im.referrerPolicy='no-referrer';
      im.src='https://'+code+'.goatcounter.com/count?p='+encodeURIComponent(p)+(isEvent?'&e=true':'&t='+encodeURIComponent(document.title))+'&s='+bucket()+',0,1&rnd='+Math.random().toString(36).slice(2,8);}catch(e){}
  }
  function ev(name){if(OK.test(name))send(name,true);}
  function pg(){return((location.pathname.split('/').pop()||'index').replace(/\.html$/i,'').toLowerCase().replace(/[^a-z]/g,''))||'index';}
  var path=location.pathname.replace(/index\.html$/i,'');if(!PATH.test(path))path='/';
  send(path||'/',false);                              // 방문 1회(주소의 경로만, 검색어·해시 제외)
  document.addEventListener('submit',function(e){
    var f=e.target;if(!f||f.id!=='medicalSearchForm')return;
    var k=document.getElementById('medicalKind'),g=document.getElementById('medicalGu'),q=document.getElementById('medicalQuery');
    if(!k||(k.value!=='pharmacy'&&k.value!=='emergency'))return;
    ev('search-'+k.value+'-'+(GU[g?g.value:'']||'all')+'-q'+((q&&q.value.trim())?1:0));   // 검색어 글자는 읽지만 보내지 않고, 썼는지(1)/안 썼는지(0)만
  },true);
  document.addEventListener('click',function(e){
    var t=e.target;if(!t||!t.closest)return;
    var a=t.closest('a[href]');
    if(a){var h=a.getAttribute('href')||'';
      if(/^tel:/i.test(h)){ev('tel-'+pg());return;}                 // 눌렀다는 기록일 뿐, 통화 연결 성공이 아님
      if(/^https:\/\/map\.(naver|kakao)\.com\//.test(h)){var k=document.getElementById('medicalKind');if(k)ev('map-'+k.value);return;}}
    var gb=t.closest('button.gu[data-gu]');if(gb){var c=GU[gb.getAttribute('data-gu')];if(c&&c!=='all')ev('gu-'+c);return;}
    var sb=t.closest('#hj-sizebar button[data-k]');if(sb)ev('size-'+sb.getAttribute('data-k'));
  },true);
})();
