/* 가족 전화 · 오늘의 안부 (v0, 시범 오픈 후보 — 테스트 브랜치)
   - 가족 이름·전화번호는 이 휴대폰(localStorage)에만 저장해요. 서버로 보내지 않아요.
   - 가족에게는 어르신이 직접 누르는 전화·문자로만 연락돼요. 자동 알림은 없어요. */
(function(root){
  var KEY='hyoja-family',KEYC='hyoja-checkin';
  function digits(v){return String(v||'').replace(/[^0-9]/g,'');}
  function validPhone(v){var d=digits(v);return /^(01[016789]\d{7,8}|02\d{7,8}|0[3-6]\d{8,9}|0[3-6]\d{1}\d{7,8}|070\d{8}|0507\d{8})$/.test(d);}
  function fmt(v){var d=digits(v);if(/^01/.test(d))return d.length===11?d.replace(/(\d{3})(\d{4})(\d{4})/,'$1-$2-$3'):d.replace(/(\d{3})(\d{3})(\d{4})/,'$1-$2-$3');
    if(/^02/.test(d))return d.length===10?d.replace(/(\d{2})(\d{4})(\d{4})/,'$1-$2-$3'):d.replace(/(\d{2})(\d{3})(\d{4})/,'$1-$2-$3');
    return d.length===11?d.replace(/(\d{3})(\d{4})(\d{4})/,'$1-$2-$3'):d.replace(/(\d{3})(\d{3})(\d{4})/,'$1-$2-$3');}
  function kstDay(now){var d=new Date((now||Date.now())+9*3600*1000);return d.toISOString().slice(0,10);}
  function smsHref(phone,text){return 'sms:'+digits(phone)+'?&body='+encodeURIComponent(text);}
  function load(st){try{var a=JSON.parse(st.getItem(KEY)||'[]');return Array.isArray(a)?a.filter(function(x){return x&&x.name&&validPhone(x.phone);}).slice(0,3):[];}catch(e){return [];}}
  function save(st,list){try{st.setItem(KEY,JSON.stringify(list.slice(0,3)));return true;}catch(e){return false;}}
  function getCheck(st,now){try{var c=JSON.parse(st.getItem(KEYC)||'null');return c&&c.day===kstDay(now)?c:null;}catch(e){return null;}}
  function setCheck(st,now){var d=new Date((now||Date.now())+9*3600*1000);var c={day:kstDay(now),at:d.toISOString().slice(11,16)};try{st.setItem(KEYC,JSON.stringify(c));}catch(e){}return c;}
  var api={digits:digits,validPhone:validPhone,fmt:fmt,kstDay:kstDay,smsHref:smsHref,load:load,save:save,getCheck:getCheck,setCheck:setCheck};
  if(typeof module!=='undefined'&&module.exports){module.exports=api;}
  root.hjFamily=api;
  if(typeof document==='undefined')return;
  var host=document.getElementById('hjFamily');if(!host)return;
  var st;try{st=root.localStorage;st.getItem('x');}catch(e){st=null;}
  var btn='min-height:60px;display:flex;align-items:center;justify-content:center;border-radius:30px;font-size:21px;font-weight:700;font-family:inherit;box-sizing:border-box;padding:8px 14px;text-align:center;border:2px solid #D9A066;';
  var card='background:#fff;border:2px solid #F0D6B5;border-radius:22px;box-shadow:0 8px 0 #E8C79B,0 16px 22px rgba(120,70,20,.16);padding:16px;display:flex;flex-direction:column;gap:10px';
  function el(t,css,txt){var e=document.createElement(t);if(css)e.style.cssText=css;if(txt!==undefined)e.textContent=txt;return e;}
  function render(editing){
    host.textContent='';
    var fam=st?load(st):[];
    // 오늘의 안부
    var c1=el('div',card);c1.appendChild(el('div','font-size:24px;font-weight:900','오늘의 안부'));
    var chk=st?getCheck(st):null;
    if(chk){c1.appendChild(el('div','font-size:20px;line-height:1.5;color:#2E6B2E;font-weight:700','✔ 이 휴대폰에 오늘 안부를 기록했어요 ('+chk.at+')'));}
    else{c1.appendChild(el('div','font-size:19px;line-height:1.5;color:#6A4A33','오늘 하루도 잘 지내고 계신가요? 아래 버튼을 누르면 이 휴대폰에 기록돼요. 가족에게 자동으로 전달되지는 않아요.'));}
    var b=el('button',btn+'background:'+(chk?'#fff':'linear-gradient(180deg,#D2691E,#A8470F)')+';color:'+(chk?'#B8501A':'#fff'),chk?'안부 한 번 더 남기기':'오늘도 잘 지내요');b.type='button';
    b.onclick=function(){if(st)setCheck(st);render(false);};c1.appendChild(b);
    if(chk&&fam.length){var t='[효자 용인] 오늘도 잘 지내고 있어요. 걱정하지 마세요.';
      fam.forEach(function(f){var a=el('a',btn+'background:#fff;color:#B8501A','문자 보내기: '+f.name+'에게 알리기');a.href=smsHref(f.phone,t);c1.appendChild(a);});}
    c1.appendChild(el('div','font-size:16px;line-height:1.5;color:#6A4A33','※ 가족에게 자동으로 알려 주는 기능은 아직 없어요. 가족이 알려면 아래 「문자로 알리기」를 직접 눌러 보내셔야 해요. 기록은 이 휴대폰에만 저장돼요.'));
    host.appendChild(c1);
    // 가족 전화
    var c2=el('div',card+';margin-top:14px');c2.appendChild(el('div','font-size:24px;font-weight:900','가족에게 전화'));
    if(!fam.length&&!editing){c2.appendChild(el('div','font-size:19px;line-height:1.5;color:#6A4A33','자주 전화하는 가족을 3명까지 저장해 둘 수 있어요.'));}
    fam.forEach(function(f){var a=el('a',btn+'background:linear-gradient(180deg,#D2691E,#A8470F);color:#fff;box-shadow:0 5px 0 #7A3510;font-size:22px',f.name+'에게 전화');a.style.flexDirection='column';a.style.gap='2px';var nn=el('span','font-size:20px;white-space:nowrap',fmt(f.phone));a.appendChild(nn);a.href='tel:'+digits(f.phone);c2.appendChild(a);});
    if(editing){
      var n=el('input',btn+'background:#fff;font-weight:500;justify-content:flex-start');n.placeholder='이름 (예: 큰딸)';n.maxLength=10;n.setAttribute('aria-label','이름');
      var p=el('input',btn+'background:#fff;font-weight:500;justify-content:flex-start');p.placeholder='전화번호 (예: 010-1234-5678)';p.inputMode='tel';p.setAttribute('aria-label','전화번호');
      var m=el('div','font-size:18px;line-height:1.5;color:#B3261E');
      var s=el('button',btn+'background:#B8501A;color:#fff','저장하기');s.type='button';
      s.onclick=function(){var nm=n.value.trim();if(!nm){m.textContent='이름을 적어 주세요.';return;}
        if(!validPhone(p.value)){m.textContent='전화번호를 다시 확인해 주세요.';return;}
        if(fam.length>=3){m.textContent='3명까지 저장할 수 있어요.';return;}
        fam.push({name:nm,phone:digits(p.value)});if(!(st&&save(st,fam))){m.textContent='이 휴대폰에서는 저장되지 않아요.';return;}render(false);};
      var x=el('button',btn+'background:#fff;color:#B8501A','닫기');x.type='button';x.onclick=function(){render(false);};
      [n,p,m,s,x].forEach(function(e){c2.appendChild(e);});
    }else{
      if(fam.length<3){var add=el('button',btn+'background:#fff;color:#B8501A','＋ 가족 저장하기');add.type='button';add.onclick=function(){render(true);};c2.appendChild(add);}
      if(fam.length){var del=el('button',btn+'background:#fff;color:#6A4A33;font-size:18px;min-height:52px','저장한 가족 지우기');del.type='button';
        del.onclick=function(){if(st)save(st,[]);render(false);};c2.appendChild(del);}
    }
    c2.appendChild(el('div','font-size:16px;line-height:1.5;color:#6A4A33','가족 이름과 번호는 이 휴대폰에만 저장되고, 외부로 전송되지 않아요.'));
    host.appendChild(c2);
  }
  render(false);
})(typeof window!=='undefined'?window:this);
