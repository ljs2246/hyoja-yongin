(function(){
  var kids=document.body.children,wrap=null;
  for(var i=0;i<kids.length;i++){if(kids[i].tagName==='DIV'){wrap=kids[i];break;}}
  if(!wrap)return;
  var f=document.createElement('div');
  f.style.cssText='margin:8px 20px 20px;padding:14px 16px;border-top:2px solid #F0D6B5;font-family:inherit;color:#6A4A33;font-size:16px;line-height:1.6;word-break:keep-all';
  var a=document.createElement('div');a.textContent='「효자 용인」은 개인이 만든 안내 사이트예요. 용인시와 관계가 없어요.';
  var b=document.createElement('div');b.textContent='공식 자료의 출처와 확인한 날짜를 함께 적었어요. 가시기 전에 꼭 한 번 더 확인해 주세요.';
  var c=document.createElement('div');c.style.cssText='margin-top:6px;font-weight:700;color:#3B2314';
  var u=['ljs2329','yahoo.co.kr'].join('@');
  c.appendChild(document.createTextNode('운영: 효자 용인 운영팀 · 문의: '));
  var m=document.createElement('a');m.href='mailto:'+u;m.textContent=u;m.style.cssText='color:#B8501A;text-decoration:underline;overflow-wrap:anywhere';
  c.appendChild(m);
  f.appendChild(a);f.appendChild(b);f.appendChild(c);
  var nav=wrap.querySelector('div[data-hjnav],div[style*="repeat(6"]');
  if(nav&&nav.parentNode)nav.parentNode.insertBefore(f,nav);else wrap.appendChild(f);
})();
