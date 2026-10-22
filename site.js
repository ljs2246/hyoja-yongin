(function(){
  var zooms={normal:1,large:1.12,xl:1.25},labels=[['normal','보통'],['large','크게'],['xl','아주 크게']];
  var wrap=null,kids=document.body.children;
  for(var i=0;i<kids.length;i++){if(kids[i].tagName==='DIV'){wrap=kids[i];break;}}
  if(!wrap)return;
  var size='normal';
  try{var sv=localStorage.getItem('hyoja-size');if(sv&&zooms[sv])size=sv;}catch(e){}
  var bar=document.createElement('div');
  bar.style.cssText='display:flex;align-items:center;gap:6px;padding:8px 12px;background:#FFF0DA;border-bottom:2px solid #F0D6B5;font-family:inherit;box-sizing:border-box;width:100%';
  var t=document.createElement('span');t.textContent='글자 크기';t.style.cssText='font-size:16px;font-weight:700;color:#6A4A33;white-space:nowrap';
  bar.appendChild(t);
  function paint(){
    wrap.style.zoom=zooms[size];
    var bs=bar.querySelectorAll('button');
    for(var i=0;i<bs.length;i++){var on=bs[i].getAttribute('data-k')===size;
      bs[i].style.background=on?'#B8501A':'#FFFFFF';bs[i].style.color=on?'#FFFFFF':'#7A3510';}
  }
  labels.forEach(function(l){
    var b=document.createElement('button');b.type='button';b.setAttribute('data-k',l[0]);b.textContent=l[1];
    b.style.cssText='flex:1;min-height:44px;border-radius:22px;border:2px solid #D9A066;font-family:inherit;font-size:16px;font-weight:700;white-space:nowrap;padding:0 4px';
    b.onclick=function(){size=l[0];try{localStorage.setItem('hyoja-size',size)}catch(e){}paint();};
    bar.appendChild(b);
  });

  // 전화 버튼: 글자가 길어도 잘리지 않게 여백을 주고, 전화번호는 한 줄로 묶어요
  var st=document.createElement('style');
  st.textContent='a[href^="tel:"]{box-sizing:border-box;padding:12px 20px;text-align:center;line-height:1.4;flex-wrap:wrap;gap:0 .4em;border-radius:30px}a[href^="tel:"] .tn{white-space:nowrap}';
  document.head.appendChild(st);
  var tl=document.querySelectorAll('a[href^="tel:"]');
  for(var j=0;j<tl.length;j++){var a=tl[j];if(a.children.length)continue;
    a.innerHTML=a.textContent.replace(/([0-9][0-9\-~]{5,})/g,'<span class="tn">$1</span>');}
  wrap.insertBefore(bar,wrap.firstChild);
  paint();
})();
