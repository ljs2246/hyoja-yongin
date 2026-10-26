/* Nationwide data isolation foundation. Not connected to public pages yet.
 * Region IDs must come from a verified registry; no inferred region names.
 */
(function(root){
 'use strict';
 var KINDS=['hospital','clinic','emergency','pharmacy','public_office','health_center','welfare_center','culture','employment','transport','business'];
 function registry(regions){
   var index=new Map();
   regions.forEach(function(r){if(!r.code||index.has(r.code))throw Error('지역 식별자 누락 또는 중복');index.set(r.code,r);});
   index.forEach(function(r){
     var seen=new Set(),current=r;
     while(current){if(seen.has(current.code))throw Error('지역 상위 관계 순환');seen.add(current.code);
       if(current.parentCode&&!index.has(current.parentCode))throw Error('상위 지역 누락');
       current=current.parentCode?index.get(current.parentCode):null;
     }
   });
   function contains(selected,actual){
     if(!index.has(selected)||!index.has(actual))return false;
     var current=index.get(actual);
     while(current){if(current.code===selected)return true;current=current.parentCode?index.get(current.parentCode):null;}
     return false;
   }
   return {contains:contains,has:function(code){return index.has(code);}};
 }
 function normal(s){return String(s||'').replace(/\s+/g,'').toLowerCase();}
 function selectInstitutions(records,selected,kind,regions){
   if(!regions.has(selected)||!KINDS.includes(kind))return {items:[],withheld:[],error:'지역 또는 기관 종류 확인 필요'};
   var idCounts=new Map(),placeCounts=new Map();
   records.forEach(function(r){
     if(r.institutionId)idCounts.set(r.institutionId,(idCounts.get(r.institutionId)||0)+1);
     var k=r.kind+'|'+normal(r.name)+'|'+normal(r.address);
     if(r.name&&r.address)placeCounts.set(k,(placeCounts.get(k)||0)+1);
   });
   var items=[],withheld=[];
   records.forEach(function(r){
     if(r.kind!==kind||!regions.contains(selected,r.regionCode))return;
     var reason=null;
     if(!r.institutionId||!r.sourceId||!r.sourceRecordId||!r.name||!r.address)reason='필수 항목 누락';
     else if(idCounts.get(r.institutionId)!==1)reason='통합 기관 식별자 중복';
     else if(r.addressRegionCode!==r.regionCode)reason='주소와 지역코드 불일치';
     else if(r.locationVerified!==true||r.kindVerified!==true||!r.verifiedAt||!r.sourceUrl)reason='위치·분류 검증 근거 미확인';
     else if(placeCounts.get(r.kind+'|'+normal(r.name)+'|'+normal(r.address))>1)reason='동명·동일 주소 중복 검토 필요';
     if(reason)withheld.push({institutionId:r.institutionId||null,reason:reason});
     else items.push(r);
   });
   return {items:items,withheld:withheld,error:null};
 }
 function appliesToRegion(benefit,selected,regions){
   if(!regions.has(selected)||benefit.scopeVerified!==true)return false;
   if(benefit.scope==='national')return true;
   return benefit.scope==='regional'&&regions.contains(benefit.regionCode,selected);
 }
 function selectionSession(){
   var selected=null,generation=0,requestId=0;
   return {
     change:function(code){selected=code;generation++;requestId++;return {regionCode:selected,generation:generation};},
     begin:function(){if(!selected)throw Error('지역 선택 필요');return {regionCode:selected,generation:generation,requestId:++requestId};},
     accepts:function(token){return Boolean(token)&&token.regionCode===selected&&token.generation===generation&&token.requestId===requestId;}
   };
 }
 var api={registry:registry,selectInstitutions:selectInstitutions,appliesToRegion:appliesToRegion,selectionSession:selectionSession};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;
 if(root)root.hjRegionCore=api;
})(typeof window==='undefined'?null:window);
