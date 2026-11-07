(function(){
 'use strict';
 var form=document.getElementById('medicalSearchForm');if(!form)return;
 var status=document.getElementById('medicalSearchStatus'),out=document.getElementById('medicalSearchResults'),more=document.getElementById('medicalSearchMore');
 var sequence=0,rows=[],shown=0,duplicateKeys=new Set(),curKind='emergency';
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
     var phone=curKind==='pharmacy'?window.hjMedicalMaps.pharmacyPhone(p.dutyTel1):window.hjMedicalMaps.emergencyPhone(p.hpid,p.dutyTel1);
     if(phone){var a=document.createElement('a');a.href='tel:'+phone;a.setAttribute('data-hj-src','공공데이터 data/emergency.json·pharmacy.json');a.setAttribute('data-hj-checked',String((window.HJ_DATA_DATE||'')||'공공데이터'));a.textContent='전화 '+p.dutyTel1;a.style.cssText='min-height:52px;display:flex;align-items:center;font-size:20px;font-weight:700;color:#96344a';card.appendChild(a);}
     else{var unknown=document.createElement('p');unknown.textContent='전화번호 확인 필요 · 지도나 공식 안내에서 확인해 주세요.';card.appendChild(unknown);}
     var note=document.createElement('p');note.textContent='등록 기관 검색 결과예요. 현재 운영·진료 가능 여부는 전화로 확인해 주세요.';note.style.fontSize='16px';card.appendChild(note);
     qualityNotes(p).forEach(function(text){var warn=document.createElement('p');warn.textContent=text;warn.style.cssText='font-size:17px;line-height:1.6;color:#86384a';card.appendChild(warn);});
     card.appendChild(window.hjMapRow(p.dutyName,p.dutyAddr,p.wgs84Lat,p.wgs84Lon));out.appendChild(card);
   });more.hidden=shown>=rows.length;
 }
 form.addEventListener('submit',function(e){
   e.preventDefault();clear();var request=sequence;
   var kind=document.getElementById('medicalKind').value,gu=document.getElementById('medicalGu').value,q=document.getElementById('medicalQuery').value.trim().toLowerCase();
   status.textContent='선택한 지역의 자료를 확인하고 있어요.';curKind=kind;
   function load(k){return fetch('data/'+(k==='pharmacy'?'pharmacy':'emergency')+'.json',{cache:'no-store'}).then(function(r){if(!r.ok)throw Error();return r.json();});}
   function compute(data,g){
     var counts=new Map();(data.목록||[]).forEach(function(p){var k=recordKey(p);counts.set(k,(counts.get(k)||0)+1);});var dup=new Set(Array.from(counts).filter(function(x){return x[1]>1;}).map(function(x){return x[0];}));
     function held(p){return dup.has(recordKey(p))||Object.keys(p).some(function(k){return /^dutyTime/.test(k)&&String(p[k])==='2500';});}
     var all=(data.목록||[]).filter(function(p){return validRegion(p,g)&&p.dutyName&&window.hjMedicalMaps.matchQuery(p.dutyName+' '+p.dutyAddr,q);});
     return {dup:dup,heldN:all.filter(held).length,rows:all.filter(function(p){return !held(p);}),data:data};}
   function show(r,note){duplicateKeys=r.dup;rows=r.rows;shown=10;var data=r.data;
     status.textContent=(note||'')+(rows.length?'검색 결과 '+rows.length+'건 · 자료 확인: '+(data['확인한 때']||'확인일 미제공')+(r.heldN?' · 공식 확인이 끝나지 않은 '+r.heldN+'곳은 목록에서 뺐어요':'')+(window.hjMedicalMaps.isStale(data['확인한 때'],Date.now(),7)?' · 자료 확인일이 오래됐어요. 반드시 전화로 먼저 확인해 주세요':''):'등록 자료에서 일치하는 기관을 찾지 못했어요. 기관이 없다는 뜻은 아니에요. 지역을 「용인시 전체」로 바꾸거나 도로명만(예: 동백중앙로 283) 입력해 보시고, 공식 의료 안내도 확인해 주세요.');render();}
   load(kind).then(function(data){
     if(request!==sequence)return;
     var first=compute(data,gu);
     if(first.rows.length||!q){curKind=kind;show(first);return;}
     /* 선택한 종류에서 못 찾으면 다른 종류(병원↔약국)에서 같은 검색어로 한 번 더 찾아 줌 */
     var other=kind==='pharmacy'?'emergency':'pharmacy',otherName=other==='pharmacy'?'약국':'응급의료기관';
     return load(other).then(function(d2){
       if(request!==sequence)return;
       var second=compute(d2,gu);
       if(second.rows.length){curKind=other;document.getElementById('medicalKind').value=other;
         show(second,'선택한 종류에서는 못 찾아서 「'+otherName+'」에서 찾았어요. · ');}
       else{curKind=kind;show(first);}
     }).catch(function(){curKind=kind;show(first);});
   }).catch(function(){if(request!==sequence)return;status.textContent='자료를 불러오지 못했어요. 다시 검색하거나 응급의료포털에서 확인해 주세요.';});
 });
 more.onclick=function(){shown+=10;render();};
 if(typeof module!=='undefined'&&module.exports)module.exports={validRegion:validRegion};
})();
