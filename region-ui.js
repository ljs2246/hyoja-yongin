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
     var label=document.getElementById('region-'+key+'-name');if(label){var sv=!!s[key];label.textContent=sv?('✓ 저장된 지역: '+name(s[key])):'저장된 지역 없음 (아래에서 골라 주세요)';
       label.style.cssText='margin:0 0 10px;padding:12px 14px;border-radius:14px;font-weight:800;font-size:19px;line-height:1.45;border:2px solid '+(sv?'#2F6B3A;background:#E7F3E8;color:#1F4F2A':'#BDA697;background:#F4EEE8;color:#5A4A44');}
     var button=document.getElementById('region-'+key+'-active');if(button)button.setAttribute('aria-pressed',String(s.active===key));
   });
   var active=current(),summary=document.getElementById('hj-region-summary');
   if(summary)summary.textContent=active?((s.active==='parents'?'부모님 지역':'내 지역')+' · '+active.name):'지역을 선택해 주세요';
   var status=document.getElementById('region-save-status');
   if(status)status.textContent=s.persistent?'선택한 지역은 이 브라우저에 저장됩니다.':'이 브라우저에서는 저장할 수 없어요. 현재 화면에서만 선택이 유지됩니다.';
   var go=document.getElementById('region-medical-link');
   if(go){go.hidden=!active;if(active){go.href='Emergency.html?gu='+encodeURIComponent(active.gu)+'#medical-search-title';go.textContent=active.name+' 병원·약국 찾기';}}
 }
 ['mine','parents'].forEach(function(key){
   var select=document.getElementById('region-'+key+'-select');
   if(select){catalog.forEach(function(r){var o=document.createElement('option');o.value=r.code;o.textContent=r.name;select.appendChild(o);});select.value=profiles.get()[key]||'';}
   var save=document.getElementById('region-'+key+'-save');if(save)save.onclick=function(){if(!select.value){document.getElementById('region-save-status').textContent='먼저 지역을 골라 주세요.';return;}profiles.select(key,select.value);profiles.activate(key);render();var nt=document.getElementById('region-'+key+'-note');if(nt)nt.textContent='✓ '+name(select.value)+' 저장했어요.';};
   if(select){var note=document.createElement('p');note.id='region-'+key+'-note';note.setAttribute('role','status');note.style.cssText='margin:0 0 10px;font-weight:700;color:#2F6B3A;min-height:0';select.parentNode.insertBefore(note,select.nextSibling);
     select.addEventListener('change',function(){if(!select.value){note.textContent='';return;}profiles.select(key,select.value);profiles.activate(key);render();note.textContent='✓ '+name(select.value)+' 저장했어요.';});}
   var active=document.getElementById('region-'+key+'-active');if(active)active.onclick=function(){profiles.activate(key);render();var nt=document.getElementById('region-'+key+'-note'),cur=profiles.get()[key];
     if(nt)nt.textContent=cur?('✓ '+(key==='parents'?'부모님 지역':'내 지역')+'을 보고 있어요: '+name(cur)+'. 아래 「병원·약국 찾기」를 눌러 주세요.'):'먼저 지역을 골라 저장해 주세요.';
     var go=document.getElementById('region-medical-link');var tgt=(cur&&go&&!go.hidden)?go:nt;if(tgt&&tgt.scrollIntoView)tgt.scrollIntoView({block:'center'});};
   var clear=document.getElementById('region-'+key+'-clear');if(clear)clear.onclick=function(){profiles.clear(key);select.value='';render();};
 });
 var gu=document.getElementById('medicalGu'),query=new URLSearchParams(location.search);
 if(gu){var row=current(),choice=query.has('gu')?query.get('gu'):row?row.gu:'';if(['','처인구','기흥구','수지구'].includes(choice))gu.value=choice;}
 window.addEventListener('pageshow',render);
 window.addEventListener('storage',function(){location.reload();});
 render();
})();
