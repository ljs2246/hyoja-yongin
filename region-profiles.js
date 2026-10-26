/* Stores region IDs only, never coordinates or street addresses.
 * Connect only after the official region registry has been validated.
 */
(function(root){
 'use strict';
 var KEY='hyoja.regionProfiles.v1';
 function create(storage,regions){
   var state={active:'mine',mine:null,parents:null},persistent=true;
   function allowed(code){return typeof code==='string'&&regions.has(code);}
   function snapshot(){return {active:state.active,mine:state.mine,parents:state.parents,persistent:persistent};}
   try{
     var raw=storage.getItem(KEY);
     if(raw){var saved=JSON.parse(raw);
       if(saved.version===1){state.active=saved.active==='parents'?'parents':'mine';state.mine=allowed(saved.mine)?saved.mine:null;state.parents=allowed(saved.parents)?saved.parents:null;}
     }
   }catch(e){persistent=false;}
   function save(){try{storage.setItem(KEY,JSON.stringify({version:1,active:state.active,mine:state.mine,parents:state.parents}));persistent=true;}catch(e){persistent=false;}return snapshot();}
   return {
     get:snapshot,
     select:function(profile,code){if(!['mine','parents'].includes(profile)||!allowed(code))throw Error('등록된 지역 선택 필요');state[profile]=code;return save();},
     activate:function(profile){if(!['mine','parents'].includes(profile))throw Error('지역 구분 확인 필요');state.active=profile;return save();},
     clear:function(profile){if(!['mine','parents'].includes(profile))throw Error('지역 구분 확인 필요');state[profile]=null;return save();}
   };
 }
 if(typeof module!=='undefined'&&module.exports)module.exports={create:create};
 if(root)root.hjRegionProfiles={create:create};
})(typeof window==='undefined'?null:window);
