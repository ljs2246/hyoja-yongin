(function(){
 'use strict';
 if(!window.hjRegionCore||!window.hjRegionProfiles||!window.hjRegionCatalog)return;
 var catalog=window.hjRegionCatalog,registry=window.hjRegionCore.registry(catalog),storage;
 try{storage=window.localStorage;}catch(e){storage={getItem:function(){throw Error();},setItem:function(){throw Error();}};}
 var profiles=window.hjRegionProfiles.create(storage,registry);
 function current(){var state=profiles.get(),id=state[state.active];return catalog.find(function(r){return r.code===id;})||null;}
 function name(code){var row=catalog.find(function(r){return r.code===code;});return row?row.name:'아직 선택하지 않았어요';}
 function render(){
   var s=profiles.get();
   ['mine','parents'].forEach(function(key){
     var label=document.getElementById('region-'+key+'-name');if(label)label.textContent=name(s[key]);
     var button=document.getElementById('region-'+key+'-active');if(button)button.setAttribute('aria-pressed',String(s.active===key));
   });
   var active=current(),summary=document.getElementById('hj-region-summary');
   if(summary)summary.textContent=(s.active==='parents'?'부모님 지역':'내 지역')+' · '+(active?active.name:'지역을 선택해 주세요');
   var status=document.getElementById('region-save-status');
   if(status)status.textContent=s.persistent?'선택한 지역은 이 브라우저에 저장됩니다.':'이 브라우저에서는 저장할 수 없어요. 현재 화면에서만 선택이 유지됩니다.';
   var go=document.getElementById('region-medical-link');
   if(go){go.hidden=!active;if(active){go.href='Emergency.html?gu='+encodeURIComponent(active.gu)+'#medical-search-title';go.textContent=active.name+' 병원·약국 찾기';}}
 }
 ['mine','parents'].forEach(function(key){
   var select=document.getElementById('region-'+key+'-select');
   if(select){catalog.forEach(function(r){var o=document.createElement('option');o.value=r.code;o.textContent=r.name;select.appendChild(o);});select.value=profiles.get()[key]||'';}
   var save=document.getElementById('region-'+key+'-save');if(save)save.onclick=function(){if(!select.value){document.getElementById('region-save-status').textContent='먼저 지역을 골라 주세요.';return;}profiles.select(key,select.value);profiles.activate(key);render();};
   var active=document.getElementById('region-'+key+'-active');if(active)active.onclick=function(){profiles.activate(key);render();};
   var clear=document.getElementById('region-'+key+'-clear');if(clear)clear.onclick=function(){profiles.clear(key);select.value='';render();};
 });
 var gu=document.getElementById('medicalGu'),query=new URLSearchParams(location.search);
 if(gu){var row=current(),choice=query.has('gu')?query.get('gu'):row?row.gu:'';if(['','처인구','기흥구','수지구'].includes(choice))gu.value=choice;}
 window.addEventListener('pageshow',render);
 window.addEventListener('storage',function(){location.reload();});
 render();
})();
