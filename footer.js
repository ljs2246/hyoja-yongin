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
  // 방문 수만 세는 통계(개인정보·쿠키 없음). 아래에 GoatCounter 코드를 넣으면 켜져요.
  var GC='';
  if(GC){var s=document.createElement('script');s.async=true;s.setAttribute('data-goatcounter','https://'+GC+'.goatcounter.com/count');s.src='https://gc.zgo.at/count.js';document.head.appendChild(s);}
})();

/* 임시 장애 차단 스위치(킬스위치): data/killswitch.json 의 active 가 true 일 때만 동작. 기본은 꺼짐.
   hide: 숨길 항목의 CSS 선택자 목록(예: 공공데이터 전화 링크). 숨긴 자리에는 notice 문구를 보여 준다.
   119·112·129 같은 표준 긴급번호는 data-hj-keep 표시가 있으면 어떤 경우에도 숨기지 않는다. 켜고 끄는 것은 승인된 사람만(저장소 쓰기 권한). */
(function(){
  try{
    fetch('data/killswitch.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(k){
      if(!k||k.active!==true||!Array.isArray(k.hide)||!k.hide.length)return;
      var css=k.hide.filter(function(s){return typeof s==='string'&&s.length<200;}).map(function(s){return s+':not([data-hj-keep])';}).join(',');
      if(!css)return;
      var st=document.createElement('style');st.setAttribute('data-hj-killswitch','1');st.textContent=css+'{display:none!important}';document.head.appendChild(st);
      var n=document.createElement('div');n.setAttribute('role','status');n.setAttribute('data-hj-killswitch-notice','1');
      n.style.cssText='margin:12px;padding:14px;border:2px solid #C0392B;border-radius:14px;background:#FFF3F0;font-size:19px;line-height:1.6';
      n.textContent=String(k.notice||'일부 정보를 확인하는 중이라 잠시 가렸어요. 급할 때는 119에 전화해 주세요.');
      document.body.insertBefore(n,document.body.firstChild);
    }).catch(function(){});
  }catch(e){}
})();
