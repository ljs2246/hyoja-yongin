(function(root){
  'use strict';
  function coord(lat,lng){
    if(lat===null||lng===null||String(lat).trim()===''||String(lng).trim()==='')return null;
    lat=Number(lat);lng=Number(lng);
    return Number.isFinite(lat)&&Number.isFinite(lng)&&lat>=31.43&&lat<=44.35&&lng>=122.37&&lng<=132?{lat:lat,lng:lng}:null;
  }
  function route(name,lat,lng,mode,ua){
    var c=coord(lat,lng);if(!c||!['walk','car','public'].includes(mode))return null;
    var action='route/'+mode+'?'+new URLSearchParams({dlat:c.lat,dlng:c.lng,dname:name,appname:'https://hyoja-yongin.com/'}).toString();
    if(/Android/i.test(ua))return 'intent://'+action+'#Intent;scheme=nmap;action=android.intent.action.VIEW;category=android.intent.category.BROWSABLE;package=com.nhn.android.nmap;end';
    return 'nmap://'+action;
  }
  function normalize(s){return String(s||'').replace(/\s+/g,'');}
  function phone(value){var n=String(value||'').replace(/[^0-9]/g,'');return /^\d{8,11}$/.test(n)&&!/0{7}$/.test(n)?n:null;}
  function hospitalMatch(list,id,address){
    var expected=normalize(address),matches=list.filter(function(p){var actual=normalize(p.dutyAddr),suffix=actual.slice(expected.length);return expected&&p.hpid===id&&actual.startsWith(expected)&&(!suffix||/^[,(]/.test(suffix))&&coord(p.wgs84Lat,p.wgs84Lon);});
    return matches.length===1?matches[0]:null;
  }
  function link(url,text){var a=document.createElement('a');a.href=url;a.textContent=text;a.style.cssText='min-height:52px;display:flex;align-items:center;justify-content:center;border-radius:16px;border:2px solid #D9A066;background:#fff;color:#96344a;font-size:18px;font-weight:700;padding:8px;text-align:center';return a;}
  function row(name,addr,lat,lng){
    var box=document.createElement('div');box.className='hj-medical-maps';
    var grid=document.createElement('div');grid.style.cssText='display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px';
    var q=encodeURIComponent((addr+' '+name).trim());
    var web=link('https://map.naver.com/p/search/'+q,'네이버 지도 검색');web.target='_blank';web.rel='noopener';grid.appendChild(web);
    var c=coord(lat,lng);
    var kakao=link(c?'https://map.kakao.com/link/map/'+encodeURIComponent(name)+','+c.lat+','+c.lng:'https://map.kakao.com/link/search/'+q,'카카오 지도');kakao.target='_blank';kakao.rel='noopener';grid.appendChild(kakao);
    if(c){[['walk','도보 길찾기'],['car','차량 길찾기'],['public','대중교통 길찾기']].forEach(function(m){
      var a=link(route(name,c.lat,c.lng,m[0],navigator.userAgent),m[1]+' ↗');a.setAttribute('aria-label',name+' 네이버 지도 앱 '+m[1]);grid.appendChild(a);
    });}
    box.appendChild(grid);
    var note=document.createElement('p');note.style.cssText='font-size:16px;line-height:1.6;color:#6A4A33;margin:10px 0 0';
    note.textContent=c?'길찾기는 네이버 지도 앱에서 열려요. 지도에서 출발지·이동수단을 확인하면 거리와 예상 시간을 볼 수 있어요. 앱이 없거나 열리지 않으면 아래 설치 안내나 지도 검색을 이용해 주세요.':'목적지 좌표를 확인하지 못해 길찾기를 제공하지 않아요. 지도 검색 결과에서 기관명과 주소를 확인해 주세요.';
    box.appendChild(note);
    if(c){var stores=/Android/i.test(navigator.userAgent)?[['https://play.google.com/store/apps/details?id=com.nhn.android.nmap','네이버 지도 앱 설치 안내']]:/iPhone|iPad|iPod/i.test(navigator.userAgent)?[['https://apps.apple.com/kr/app/id311867728','네이버 지도 앱 설치 안내']]:[['https://play.google.com/store/apps/details?id=com.nhn.android.nmap','안드로이드 앱 설치 안내'],['https://apps.apple.com/kr/app/id311867728','아이폰 앱 설치 안내']];stores.forEach(function(s){var install=link(s[0],s[1]);install.target='_blank';install.rel='noopener';box.appendChild(install);});}
    var details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='주소 확인·복사';summary.style.cssText='padding:12px 0;font-size:17px;cursor:pointer';details.appendChild(summary);
    var address=document.createElement('p');address.textContent=addr;details.appendChild(address);
    var copy=document.createElement('button');copy.type='button';copy.textContent='주소 복사';copy.style.cssText='min-height:48px;font:inherit;padding:8px 16px;border-radius:12px;border:1px solid #D9A066;background:#fff;color:#96344a';
    var status=document.createElement('p');status.setAttribute('role','status');
    copy.onclick=function(){if(!navigator.clipboard){status.textContent='위 주소를 선택해 복사해 주세요.';return;}navigator.clipboard.writeText(addr).then(function(){status.textContent='주소를 복사했어요.';},function(){status.textContent='위 주소를 선택해 복사해 주세요.';});};details.appendChild(copy);details.appendChild(status);box.appendChild(details);
    return box;
  }
  var api={coord:coord,route:route,phone:phone,hospitalMatch:hospitalMatch,row:row};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root){root.hjMedicalMaps=api;root.hjMapRow=row;}
})(typeof window==='undefined'?null:window);
