const V='hyoja-v38';
const CORE=['./','index.html','Emergency.html','All.html','Centers.html','Culture.html','Guide.html','Health.html','Jobs.html','Transit.html','Welfare.html','Ad.html','Ad2.html','site.js','theme.css','events.js','family.js','Regions.html','region-core.js','region-profiles.js','region-catalog.js','region-ui.js','medical-maps.js','medical-search.js','assets/family-final.webp','assets/hyoja-ruby-coral.png','footer.js','read.js','places.js','sound.js','manifest.webmanifest','icon-192.png','icon-512.png','apple-touch-icon.png','data/pharmacy.json','data/emergency.json'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>Promise.all(CORE.map(u=>c.add(u).catch(()=>{})))).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==V).map(x=>caches.delete(x)))).then(()=>self.clients.claim()));});
function nf(req){return new Promise(res=>{let done=false;
  const t=setTimeout(async()=>{const m=await caches.match(req,{ignoreSearch:true});if(m&&!done){done=true;res(m);}},4000);
  fetch(req,{cache:'no-cache'}).then(r=>{clearTimeout(t);if(r&&r.ok){const c=r.clone();caches.open(V).then(x=>x.put(req,c));}if(!done){done=true;res(r);}})
   .catch(async()=>{clearTimeout(t);const m=await caches.match(req,{ignoreSearch:true});if(!done){done=true;res(m||Response.error());}});});}
self.addEventListener('fetch',e=>{const r=e.request;if(r.method!=='GET')return;const u=new URL(r.url);if(u.origin!==location.origin)return;e.respondWith(nf(r));});



