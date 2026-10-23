// 버튼을 누를 때 짧은 소리를 내고, 켜고 끄기·크기 조절을 할 수 있게 해요.
(function(){
  var on=true,vol=0.6,ctx=null;
  try{var s=JSON.parse(localStorage.getItem('hyoja-snd')||'null');if(s){on=s.on!==false;if(typeof s.vol==='number')vol=Math.max(0,Math.min(1,s.vol));}}catch(e){}
  function save(){try{localStorage.setItem('hyoja-snd',JSON.stringify({on:on,vol:vol}));}catch(e){}}
  function beep(){
    if(!on||vol<=0)return;
    try{if(navigator.audioSession)navigator.audioSession.type='playback';}catch(e){}
    try{var AC=window.AudioContext||window.webkitAudioContext;if(!AC)return;
      if(!ctx)ctx=new AC();if(ctx.state==='suspended')ctx.resume();
      var o=ctx.createOscillator(),g=ctx.createGain(),t=ctx.currentTime;
      o.type='sine';o.frequency.setValueAtTime(880,t);o.frequency.exponentialRampToValueAtTime(1175,t+0.08);
      g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(Math.max(0.001,vol*0.5),t+0.01);g.gain.exponentialRampToValueAtTime(0.0001,t+0.14);
      o.connect(g);g.connect(ctx.destination);o.start(t);o.stop(t+0.16);}catch(e){}
  }
  document.addEventListener('click',function(e){
    var el=e.target&&e.target.closest?e.target.closest('a,button'):null;
    if(!el||el.closest('#hj-sndbar'))return;
    beep();
    // 링크는 소리가 끝난 뒤에 이동해요 (바로 이동하면 소리가 잘려요)
    var h=el.tagName==='A'?el.getAttribute('href'):null;
    if(on&&vol>0&&h&&!/^(#|tel:|sms:|mailto:|intent:|javascript:)/i.test(h)&&el.target!=='_blank'&&!e.ctrlKey&&!e.metaKey&&!e.shiftKey&&e.button===0){
      e.preventDefault();var u=el.href;setTimeout(function(){location.href=u;},170);
    }
  },true);
  var wrap=null,kids=document.body.children;
  for(var i=0;i<kids.length;i++){if(kids[i].tagName==='DIV'){wrap=kids[i];break;}}
  if(!wrap)return;
  var bar=document.createElement('div');bar.id='hj-sndbar';
  bar.style.cssText='display:flex;align-items:center;gap:8px;padding:8px 12px;background:#FFF0DA;border-bottom:2px solid #F0D6B5;font-family:inherit;box-sizing:border-box;width:100%';
  var lb=document.createElement('span');lb.textContent='버튼 소리';lb.style.cssText='font-size:16px;font-weight:700;color:#6A4A33;white-space:nowrap';
  var tg=document.createElement('button');tg.type='button';
  tg.style.cssText='min-height:44px;min-width:64px;border-radius:22px;border:2px solid #D9A066;font-family:inherit;font-size:16px;font-weight:700;padding:0 10px;white-space:nowrap';
  var rg=document.createElement('input');rg.type='range';rg.min='0';rg.max='100';rg.step='5';rg.value=String(Math.round(vol*100));
  rg.setAttribute('aria-label','버튼 소리 크기');rg.style.cssText='flex:1;min-width:0;height:44px;accent-color:#B8501A';
  function paint(){tg.textContent=on?'켜짐':'꺼짐';tg.style.background=on?'#B8501A':'#FFFFFF';tg.style.color=on?'#FFFFFF':'#7A3510';rg.disabled=!on;rg.style.opacity=on?'1':'.4';}
  tg.onclick=function(){on=!on;save();paint();if(on)beep();};
  rg.oninput=function(){vol=rg.value/100;save();};
  rg.onchange=function(){beep();};
  bar.appendChild(lb);bar.appendChild(tg);bar.appendChild(rg);paint();
  var ref=document.getElementById('hj-readbar')||document.getElementById('hj-sizebar');
  if(ref&&ref.parentNode)ref.parentNode.insertBefore(bar,ref.nextSibling);else wrap.insertBefore(bar,wrap.firstChild);
})();
