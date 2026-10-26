(function(){
  if(!('speechSynthesis' in window)||!window.SpeechSynthesisUtterance)return;
  var kids=document.body.children,wrap=null;
  for(var i=0;i<kids.length;i++){if(kids[i].tagName==='DIV'){wrap=kids[i];break;}}
  if(!wrap)return;
  var bar=document.createElement('div');bar.id='hj-readbar';
  bar.style.cssText='padding:8px 12px;background:#FFF0DA;border-bottom:2px solid #F0D6B5;box-sizing:border-box;width:100%;font-family:inherit';
  var btn=document.createElement('button');btn.type='button';
  btn.style.cssText='width:100%;min-height:48px;border-radius:24px;border:2px solid #D9A066;background:#fff;color:#7A3510;font-family:inherit;font-size:18px;font-weight:700;box-shadow:0 4px 0 #E8C79B';
  var msg=document.createElement('div');msg.style.cssText='font-size:15px;color:#6A4A33;margin-top:6px;display:none';
  bar.appendChild(btn);bar.appendChild(msg);
  var sb=document.getElementById('hj-sizebar');
  if(sb&&sb.parentNode)sb.parentNode.insertBefore(bar,sb.nextSibling);else wrap.insertBefore(bar,wrap.firstChild);
  var speaking=false,queue=[];
  function label(){btn.textContent=speaking?'멈추기':'소리로 읽어 주기';btn.setAttribute('aria-pressed',speaking?'true':'false');}
  function skip(n){var e=n.parentNode;while(e&&e!==wrap){
    if(e.id==='hj-sizebar'||e.id==='hj-readbar'||e.id==='hj-sndbar'||e.hasAttribute&&(e.hasAttribute('data-hjnav')||e.hasAttribute('data-hjfoot')))return true;
    // A child can have display:block even when its ancestor is hidden.
    if(e.hidden||e.getAttribute&&e.getAttribute('aria-hidden')==='true')return true;
    var style=getComputedStyle(e);
    if(style.display==='none'||style.visibility==='hidden'||style.visibility==='collapse')return true;
    var t=e.tagName;if(t==='SCRIPT'||t==='STYLE'||t==='SVG'||t==='svg'||t==='NOSCRIPT')return true;
    e=e.parentNode;}return false;}
  function collect(){
    var w=document.createTreeWalker(wrap,NodeFilter.SHOW_TEXT,null),out=[],n;
    while((n=w.nextNode())){var t=n.textContent.replace(/\s+/g,' ').trim();if(!t||skip(n))continue;
      var st=n.parentNode&&getComputedStyle(n.parentNode);if(st&&(st.display==='none'||st.visibility==='hidden'))continue;
      out.push(t);}
    var text=out.map(function(t){return /[.!?。…요다까]$/.test(t)?t:t+'.';}).join(' ');
    text=text.replace(/\b119\b/g,'일일구').replace(/\b112\b/g,'일일이').replace(/\b129\b/g,'일이구')
      .replace(/(\d)-(\d)/g,'$1 $2').replace(/(\d)-(\d)/g,'$1 $2').replace(/[「」]/g,'').replace(/(^|[.\s])[·•]\s*/g,'$1').replace(/[·•]/g,', ').replace(/\s{2,}/g,' ');
    var parts=text.split(/(?<=[.!?])\s+/),chunks=[],cur='';
    parts.forEach(function(p){if((cur+' '+p).length>110&&cur){chunks.push(cur);cur=p;}else cur=cur?cur+' '+p:p;});
    if(cur)chunks.push(cur);return chunks;}
  function pickVoice(){var v=speechSynthesis.getVoices()||[];for(var i=0;i<v.length;i++){if(/^ko/i.test(v[i].lang))return v[i];}return null;}
  function next(){
    if(!speaking||!queue.length){speaking=false;label();return;}
    var u=new SpeechSynthesisUtterance(queue.shift());u.lang='ko-KR';u.rate=0.9;
    var v=pickVoice();if(v)u.voice=v;
    u.onend=next;u.onerror=function(){speaking=false;label();msg.style.display='block';msg.textContent='이 폰에서는 소리 읽기가 잘 되지 않아요.';};
    speechSynthesis.speak(u);}
  function stop(){speaking=false;queue=[];try{speechSynthesis.cancel();}catch(e){}label();}
  btn.onclick=function(){
    if(speaking){stop();return;}
    msg.style.display='none';queue=collect();
    if(!queue.length){msg.style.display='block';msg.textContent='읽을 내용이 없어요.';return;}
    speaking=true;label();try{speechSynthesis.cancel();}catch(e){}next();};
  window.addEventListener('pagehide',stop);
  label();
})();
