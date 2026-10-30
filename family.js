/* 가족 전화 (v1 견본 — 지시 022: 안부 기록·위치 기능 제외, 전화+가족 사진 중심, 테스트 브랜치)
   - 가족 이름·전화번호는 이 휴대폰(localStorage)에만 저장해요. 서버로 보내지 않아요.
   - 가족 사진도 이 휴대폰에만 작게 줄여 저장해요(서버 전송 없음). 위치·자동 알림 기능은 없어요. */
(function(root){
  var KEY='hyoja-family',KEYC='hyoja-checkin'; /* KEYC: 옛 안부 기록 — 열 때 지움 */
  function digits(v){return String(v||'').replace(/[^0-9]/g,'');}
  function validPhone(v){var d=digits(v);return /^(01[016789]\d{7,8}|02\d{7,8}|0[3-6]\d{8,9}|0[3-6]\d{1}\d{7,8}|070\d{8}|0507\d{8})$/.test(d);}
  function fmt(v){var d=digits(v);if(/^01/.test(d))return d.length===11?d.replace(/(\d{3})(\d{4})(\d{4})/,'$1-$2-$3'):d.replace(/(\d{3})(\d{3})(\d{4})/,'$1-$2-$3');
    if(/^02/.test(d))return d.length===10?d.replace(/(\d{2})(\d{4})(\d{4})/,'$1-$2-$3'):d.replace(/(\d{2})(\d{3})(\d{4})/,'$1-$2-$3');
    return d.length===11?d.replace(/(\d{3})(\d{4})(\d{4})/,'$1-$2-$3'):d.replace(/(\d{3})(\d{3})(\d{4})/,'$1-$2-$3');}
  function smsHref(phone,text){return 'sms:'+digits(phone)+'?&body='+encodeURIComponent(text);}
  function okPhoto(p){return typeof p==='string'&&/^data:image\/jpeg;base64,[A-Za-z0-9+\/=]+$/.test(p)&&p.length<60000;}
  function load(st){try{var a=JSON.parse(st.getItem(KEY)||'[]');return Array.isArray(a)?a.filter(function(x){return x&&x.name&&validPhone(x.phone);}).map(function(x){var o={name:String(x.name).slice(0,10),phone:digits(x.phone)};if(okPhoto(x.photo))o.photo=x.photo;return o;}).slice(0,3):[];}catch(e){return [];}}
  function save(st,list){try{st.setItem(KEY,JSON.stringify(list.slice(0,3)));return true;}catch(e){return false;}}
  var api={digits:digits,validPhone:validPhone,fmt:fmt,smsHref:smsHref,okPhoto:okPhoto,load:load,save:save};
  if(typeof module!=='undefined'&&module.exports){module.exports=api;}
  root.hjFamily=api;
  if(typeof document==='undefined')return;
  var host=document.getElementById('hjFamily');if(!host)return;
  var st;try{st=root.localStorage;st.getItem('x');st.removeItem(KEYC);}catch(e){st=null;}
  var btn='min-height:60px;display:flex;align-items:center;justify-content:center;border-radius:30px;font-size:21px;font-weight:700;font-family:inherit;box-sizing:border-box;padding:8px 14px;text-align:center;border:2px solid #D9A066;';
  var card='background:#fff;border:2px solid #F0D6B5;border-radius:22px;box-shadow:0 8px 0 #E8C79B,0 16px 22px rgba(120,70,20,.16);padding:16px;display:flex;flex-direction:column;gap:12px';
  function el(t,css,txt){var e=document.createElement(t);if(css)e.style.cssText=css;if(txt!==undefined)e.textContent=txt;return e;}
  function avatar(f,size){var box=el('div','width:'+size+'px;height:'+size+'px;border-radius:50%;overflow:hidden;flex:none;background:#F8E8D7;border:3px solid #E8C79B;display:flex;align-items:center;justify-content:center;font-size:'+Math.round(size*.45)+'px;font-weight:900;color:#B8501A');
    if(f.photo){var im=el('img','width:100%;height:100%;object-fit:cover');im.src=f.photo;im.alt=f.name+' 사진';box.appendChild(im);}else{box.textContent=f.name.slice(0,1);box.setAttribute('aria-hidden','true');}return box;}
  function shrink(file,cb){try{var r=new FileReader();r.onerror=function(){cb(null);};r.onload=function(){var im=new Image();im.onerror=function(){cb(null);};im.onload=function(){
    var S=160,c=document.createElement('canvas');c.width=S;c.height=S;var g=c.getContext('2d');var m=Math.min(im.width,im.height);g.drawImage(im,(im.width-m)/2,(im.height-m)/2,m,m,0,0,S,S);
    var d=c.toDataURL('image/jpeg',0.7);cb(okPhoto(d)?d:null);};im.src=r.result;};r.readAsDataURL(file);}catch(e){cb(null);}}
  function render(editing){
    host.textContent='';
    var fam=st?load(st):[];
    var c2=el('div',card);c2.appendChild(el('div','font-size:24px;font-weight:900','가족에게 전화'));
    if(!fam.length&&!editing){c2.appendChild(el('div','font-size:19px;line-height:1.5;color:#6A4A33','자주 전화하는 가족을 3명까지 저장해 두면, 사진을 보고 한 번에 전화할 수 있어요.'));}
    fam.forEach(function(f){var row=el('div','display:flex;align-items:center;gap:12px');row.appendChild(avatar(f,76));
      var a=el('a',btn+'flex:1;min-width:0;background:linear-gradient(180deg,#D2691E,#A8470F);color:#fff;box-shadow:0 5px 0 #7A3510;font-size:22px;flex-direction:column;gap:2px;min-height:76px',f.name+'에게 전화');
      a.appendChild(el('span','font-size:20px;white-space:nowrap',fmt(f.phone)));a.href='tel:'+digits(f.phone);a.setAttribute('aria-label',f.name+'에게 전화 걸기 '+fmt(f.phone));row.appendChild(a);c2.appendChild(row);});
    if(editing){
      var photo=null;
      var n=el('input',btn+'background:#fff;font-weight:500;justify-content:flex-start');n.placeholder='이름 (예: 큰딸)';n.maxLength=10;n.setAttribute('aria-label','이름');
      var p=el('input',btn+'background:#fff;font-weight:500;justify-content:flex-start');p.placeholder='전화번호 (예: 010-1234-5678)';p.inputMode='tel';p.setAttribute('aria-label','전화번호');
      var prev=el('div','display:flex;align-items:center;gap:12px');var pv=avatar({name:'?'},76);prev.appendChild(pv);
      var pick=el('label',btn+'flex:1;background:#fff;color:#B8501A;cursor:pointer','사진 고르기 (없어도 돼요)');
      var fi=el('input','position:absolute;opacity:0;width:1px;height:1px');fi.type='file';fi.accept='image/*';fi.setAttribute('aria-label','가족 사진 고르기');pick.appendChild(fi);prev.appendChild(pick);
      var m=el('div','font-size:18px;line-height:1.5;color:#B3261E');m.setAttribute('role','status');
      fi.onchange=function(){var file=fi.files&&fi.files[0];if(!file)return;shrink(file,function(d){if(!d){m.textContent='사진을 불러오지 못했어요. 사진 없이도 저장할 수 있어요.';return;}photo=d;m.textContent='';var nv=avatar({name:'?',photo:d},76);prev.replaceChild(nv,pv);pv=nv;});};
      var s=el('button',btn+'background:#B8501A;color:#fff','저장하기');s.type='button';
      s.onclick=function(){var nm=n.value.trim();if(!nm){m.textContent='이름을 적어 주세요.';return;}
        if(!validPhone(p.value)){m.textContent='전화번호를 다시 확인해 주세요.';return;}
        if(fam.length>=3){m.textContent='3명까지 저장할 수 있어요.';return;}
        if(fam.some(function(x){return x.phone===digits(p.value);})){m.textContent='이미 저장된 번호예요.';return;}
        var o={name:nm,phone:digits(p.value)};if(photo)o.photo=photo;fam.push(o);
        if(!(st&&save(st,fam))){fam.pop();if(o.photo){delete o.photo;fam.push(o);if(st&&save(st,fam)){m.textContent='';render(false);return;}fam.pop();}m.textContent='이 휴대폰에서는 저장되지 않아요.';return;}render(false);};
      var x=el('button',btn+'background:#fff;color:#B8501A','닫기');x.type='button';x.onclick=function(){render(false);};
      [n,p,prev,m,s,x].forEach(function(e){c2.appendChild(e);});
    }else{
      if(fam.length<3){var add=el('button',btn+'background:#fff;color:#B8501A','＋ 가족 저장하기');add.type='button';add.onclick=function(){render(true);};c2.appendChild(add);}
      if(fam.length){var del=el('button',btn+'background:#fff;color:#6A4A33;font-size:18px;min-height:52px','저장한 가족 지우기');del.type='button';
        del.onclick=function(){if(st)save(st,[]);render(false);};c2.appendChild(del);}
    }
    c2.appendChild(el('div','font-size:16px;line-height:1.5;color:#6A4A33','가족 이름·번호·사진은 이 휴대폰에만 저장되고, 외부로 전송되지 않아요. 위치는 사용하지 않아요.'));
    host.appendChild(c2);
  }
  render(false);
})(typeof window!=='undefined'?window:this);
