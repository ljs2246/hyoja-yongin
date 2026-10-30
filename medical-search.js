(function(){
 'use strict';
 var form=document.getElementById('medicalSearchForm');if(!form)return;
 var status=document.getElementById('medicalSearchStatus'),out=document.getElementById('medicalSearchResults'),more=document.getElementById('medicalSearchMore');
 var sequence=0,rows=[],shown=0,duplicateKeys=new Set();
 function recordKey(p){return String(p.dutyName||'').replace(/\s+/g,'')+'|'+String(p.dutyAddr||'').replace(/\s+/g,'');}
 function qualityNotes(p){var notes=[];if(duplicateKeys.has(recordKey(p)))notes.push('같은 이름·주소의 등록 자료가 중복돼 있어요. 현재 기관 정보를 다시 확인해 주세요.');
 Object.keys(p).some(function(k){return /^dutyTime/.test(k)&&String(p[k])==='2500';})&&notes.push('운영시간 원천에 해석 미확인 값이 있어요. 심야 운영 여부는 전화로 확인해 주세요.');return notes;}
 function validRegion(p,gu){
   var address=String(p.dutyAddr||'');
   return /^경기도\s+용인시\s+(처인구|기흥구|수지구)(?:\s|$)/.test(address)&&(!gu||address.startsWith('경기도 용인시 '+gu+' '));
 }
 function clear(){sequence++;rows=[];shown=0;out.textContent='';more.hidden=true;status.textContent='조건을 바꿨어요. 검색하기를 눌러 주세요.';}
 ['medicalKind','medicalGu','medicalQuery'].forEach(function(id){document.getElementById(id).addEventListener(id==='medicalQuery'?'input':'change',clear);});
 function render(){
   out.textContent='';
   rows.slice(0,shown).forEach(function(p){
     var card=document.createElement('article');card.style.cssText='padding:14px;border:1px solid #e5d2c3;border-radius:16px';
     var name=document.createElement('h3');name.textContent=p.dutyName;name.style.cssText='font-size:22px;margin:0 0 8px';card.appendChild(name);
     var addr=document.createElement('p');addr.textContent=p.dutyAddr;card.appendChild(addr);
     var phone=window.hjMedicalMaps.phone(p.dutyTel1);
     if(phone){var a=document.createElement('a');a.href='tel:'+phone;a.textContent='전화 '+p.dutyTel1;a.style.cssText='min-height:52px;display:flex;align-items:center;font-size:20px;font-weight:700;color:#96344a';card.appendChild(a);}
     else{var unknown=document.createElement('p');unknown.textContent='전화번호 확인 필요 · 지도나 공식 안내에서 확인해 주세요.';card.appendChild(unknown);}
     var note=document.createElement('p');note.textContent='등록 기관 검색 결과예요. 현재 운영·진료 가능 여부는 전화로 확인해 주세요.';note.style.fontSize='16px';card.appendChild(note);
     qualityNotes(p).forEach(function(text){var warn=document.createElement('p');warn.textContent=text;warn.style.cssText='font-size:17px;line-height:1.6;color:#86384a';card.appendChild(warn);});
     card.appendChild(window.hjMapRow(p.dutyName,p.dutyAddr,p.wgs84Lat,p.wgs84Lon));out.appendChild(card);
   });more.hidden=shown>=rows.length;
 }
 form.addEventListener('submit',function(e){
   e.preventDefault();clear();var request=sequence;
   var kind=document.getElementById('medicalKind').value,gu=document.getElementById('medicalGu').value,q=document.getElementById('medicalQuery').value.trim().toLowerCase();
   status.textContent='선택한 지역의 자료를 확인하고 있어요.';
   fetch('data/'+(kind==='pharmacy'?'pharmacy':'emergency')+'.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw Error();return r.json();}).then(function(data){
     if(request!==sequence)return;
     var counts=new Map();(data.목록||[]).forEach(function(p){var k=recordKey(p);counts.set(k,(counts.get(k)||0)+1);});duplicateKeys=new Set(Array.from(counts).filter(function(x){return x[1]>1;}).map(function(x){return x[0];}));
     function held(p){return duplicateKeys.has(recordKey(p))||Object.keys(p).some(function(k){return /^dutyTime/.test(k)&&String(p[k])==='2500';});}
     var all=(data.목록||[]).filter(function(p){return validRegion(p,gu)&&p.dutyName&&(!q||(p.dutyName+' '+p.dutyAddr).toLowerCase().includes(q));});
     var heldN=all.filter(held).length;rows=all.filter(function(p){return !held(p);});
     shown=10;status.textContent=rows.length?'검색 결과 '+rows.length+'건 · 자료 확인: '+(data['확인한 때']||'확인일 미제공')+(heldN?' · 공식 확인이 끝나지 않은 '+heldN+'곳은 목록에서 뺐어요':''):'등록 자료에서 일치하는 기관을 찾지 못했어요. 기관이 없다는 뜻은 아니에요. 검색어나 공식 의료 안내를 확인해 주세요.';render();
   }).catch(function(){if(request!==sequence)return;status.textContent='자료를 불러오지 못했어요. 다시 검색하거나 응급의료포털에서 확인해 주세요.';});
 });
 more.onclick=function(){shown+=10;render();};
 if(typeof module!=='undefined'&&module.exports)module.exports={validRegion:validRegion};
})();
