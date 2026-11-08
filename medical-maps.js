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
  function phone(value){var n=String(value||'').replace(/[^0-9]/g,'');if(/^(01\d|060|080|700)/.test(n))return null;/* 휴대전화·유료/수신자부담 번호는 기관 번호로 인정하지 않음 */return (/^\d{8,11}$/.test(n)||/^050\d{9}$/.test(n))&&!/0{7}$/.test(n)?n:null;}
  /* 약국 전화 버튼은 공식기관 확인·최종 승인된 번호만 허용(기본: 빈 목록=전부 숨김). 승인 번호는 숫자만 적는다. */
  var PHARMACY_PHONE_APPROVED=[];
  // 검색어 일치: 띄어쓰기·대소문자 무시, 여러 단어는 모두 들어 있어야 일치(예: '기흥 내과' → 기흥 주소의 내과). 빈 검색어는 전부 일치.
  function matchQuery(text,q){var t=String(text||'').toLowerCase().replace(/\s+/g,'');var w=String(q||'').toLowerCase().split(/\s+/).filter(Boolean);for(var i=0;i<w.length;i++){if(t.indexOf(w[i])<0)return false;}return true;}
  /* 응급의료기관 검색의 전화 버튼은 허용목록(기관 코드 hpid → 승인 번호)과 정확히 일치할 때만 표시. 형식이 맞아도 목록에 없으면 숨김. docs/phone-allowlist.json 과 같아야 하며 scripts/check-allowlist.py 가 검사. */
  var EMERGENCY_PHONE_APPROVED={'A2100019':['03180212114'],'A2100122':['0313370114'],'A2100029':['0313000114']};
  function emergencyPhone(hpid,value){var n=phone(value);return n&&(EMERGENCY_PHONE_APPROVED[String(hpid||'')]||[]).indexOf(n)>=0?n:null;}
  function pharmacyPhone(value){var n=phone(value);return n&&PHARMACY_PHONE_APPROVED.indexOf(n)>=0?n:null;}
  /* 자료 확인일이 limit일을 넘으면 true. 날짜 해석 불가도 true(안전 쪽). */
  function isStale(dateText,nowMs,limit){var m=/^(\d{4})-(\d{2})-(\d{2})/.exec(String(dateText||''));if(!m)return true;var t=Date.UTC(+m[1],+m[2]-1,+m[3]);return (nowMs-t)/86400000>(limit||7);}
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
    note.textContent=c?'좌표는 수집 자료 기준이며 실제 건물 위치 일치는 미확인입니다. 지도에서 기관명·주소가 맞는지 먼저 확인해 주세요. 길찾기는 네이버 지도 앱에서 열려요. 지도에서 출발지·이동수단을 확인하면 거리와 예상 시간을 볼 수 있어요. 앱이 없거나 열리지 않으면 아래 설치 안내나 지도 검색을 이용해 주세요.':'목적지 좌표를 확인하지 못해 길찾기를 제공하지 않아요. 지도 검색 결과에서 기관명과 주소를 확인해 주세요.';
    box.appendChild(note);
    if(c){var stores=/Android/i.test(navigator.userAgent)?[['https://play.google.com/store/apps/details?id=com.nhn.android.nmap','네이버 지도 앱 설치 안내']]:/iPhone|iPad|iPod/i.test(navigator.userAgent)?[['https://apps.apple.com/kr/app/id311867728','네이버 지도 앱 설치 안내']]:[['https://play.google.com/store/apps/details?id=com.nhn.android.nmap','안드로이드 앱 설치 안내'],['https://apps.apple.com/kr/app/id311867728','아이폰 앱 설치 안내']];stores.forEach(function(s){var install=link(s[0],s[1]);install.target='_blank';install.rel='noopener';box.appendChild(install);});}
    var details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='주소 확인·복사';summary.style.cssText='padding:12px 0;font-size:17px;cursor:pointer';details.appendChild(summary);
    var address=document.createElement('p');address.textContent=addr;details.appendChild(address);
    var copy=document.createElement('button');copy.type='button';copy.textContent='주소 복사';copy.style.cssText='min-height:48px;font:inherit;padding:8px 16px;border-radius:12px;border:1px solid #D9A066;background:#fff;color:#96344a';
    var status=document.createElement('p');status.setAttribute('role','status');
    copy.onclick=function(){if(!navigator.clipboard){status.textContent='위 주소를 선택해 복사해 주세요.';return;}navigator.clipboard.writeText(addr).then(function(){status.textContent='주소를 복사했어요.';},function(){status.textContent='위 주소를 선택해 복사해 주세요.';});};details.appendChild(copy);details.appendChild(status);box.appendChild(details);
    return box;
  }
  var api={coord:coord,route:route,phone:phone,pharmacyPhone:pharmacyPhone,emergencyPhone:emergencyPhone,isStale:isStale,matchQuery:matchQuery,hospitalMatch:hospitalMatch,row:row};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  if(root){root.hjMedicalMaps=api;root.hjMapRow=row;}
})(typeof window==='undefined'?null:window);
