// 복지관·보건소 등 이름이 있는 곳에 "지도·길찾기" 버튼을 붙여요. 좌표를 추측하지 않고 이름으로 지도를 열어요.
(function(){
  function mk(href,t){var a=document.createElement('a');a.href=href;a.target='_blank';a.rel='noopener';a.textContent=t;
    a.style.cssText='min-height:52px;display:flex;align-items:center;justify-content:center;text-align:center;border-radius:26px;border:2px solid #D9A066;background:#fff;color:#B8501A;font-size:17px;font-weight:700;box-sizing:border-box;padding:6px 8px';return a;}
  var links=document.querySelectorAll('a[href^="tel:"]');
  for(var i=0;i<links.length;i++){
    var a=links[i],t=a.textContent.trim(),col=a.parentNode;
    if(!col||a.getAttribute('data-hjplace')||!/flex-direction: ?column/.test(col.getAttribute('style')||''))continue;
    var card=a.closest('div[style*="border-radius: 22px"]'),ct=card?card.textContent:'',q='';
    var m=t.match(/(처인|기흥|수지)노인복지관/);
    if(m)q='용인 '+m[1]+'노인복지관';
    else if(/용인시니어클럽/.test(t))q='용인시니어클럽';
    else if(/백남준아트센터/.test(t))q='백남준아트센터';
    else if(/용인자연휴양림/.test(t))q='용인자연휴양림';
    else if(/^(처인|기흥|수지)구 /.test(t)){var g=t.slice(0,3);
      if(/치매안심센터/.test(ct))q='용인시 '+g+' 치매안심센터';
      else if(/보건소/.test(ct))q='용인시 '+g+' 보건소';}
    else if(/^전화 /.test(t)&&/용인시박물관/.test(ct))q='용인시박물관';
    if(!q)continue;
    a.setAttribute('data-hjplace','1');
    var d=document.createElement('div');d.style.cssText='display:grid;grid-template-columns:1fr 1fr;gap:8px';
    var e=encodeURIComponent(q);
    d.appendChild(mk('https://map.naver.com/p/search/'+e,'네이버 지도·길찾기'));
    d.appendChild(mk('https://map.kakao.com/link/search/'+e,'카카오맵 길찾기'));
    a.parentNode.insertBefore(d,a.nextSibling);
  }
})();
