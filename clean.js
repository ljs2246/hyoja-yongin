/* 약국 자료 점검: 번호가 가짜(000)거나 형식이 이상하면 번호를 숨기고, 이름·주소가 같은 중복은 한 곳만 보여요. */
(function(root){
  function telOk(v){var d=String(v||'').replace(/[^0-9]/g,'');
    if(!d||/^0*$/.test(d.replace(/^0\d{1,2}/,'')))return false;
    if(/^(0\d{1,2})0{4}\d{4}$/.test(d)||/^0\d{1,2}0000\d{4}$/.test(d)||/000-?0000/.test(String(v)))return false;
    return /^(01[016789]\d{7,8}|02\d{7,8}|0[3-6]\d{1}\d{7,8}|070\d{8}|0507\d{8}|1[5-9]\d{2}\d{4})$/.test(d);}
  function coordOk(la,lo){la=parseFloat(la);lo=parseFloat(lo);return la>=37.0&&la<=37.5&&lo>=127.0&&lo<=127.5;}
  function clean(list){var seen={},out=[],stat={중복제외:0,번호숨김:0,좌표숨김:0};
    (list||[]).forEach(function(p){var k=(p.dutyName||'').trim()+'|'+(p.dutyAddr||'').trim();
      if(!p.dutyName||!p.dutyAddr||seen[k]){stat.중복제외++;return;}seen[k]=1;
      var q={};for(var i in p)q[i]=p[i];
      if(!telOk(q.dutyTel1)){if(q.dutyTel1)stat.번호숨김++;q.dutyTel1='';}
      else{var dg=String(q.dutyTel1).replace(/[^0-9]/g,'');if(/^0507\d{8}$/.test(dg))q.dutyTel1=dg.replace(/(\d{4})(\d{4})(\d{4})/,'$1-$2-$3');}
      if(!coordOk(q.wgs84Lat,q.wgs84Lon)){stat.좌표숨김++;q.wgs84Lat='';q.wgs84Lon='';}
      out.push(q);});
    return {list:out,stat:stat};}
  var api={telOk:telOk,coordOk:coordOk,clean:clean};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.hjClean=api;
})(typeof window!=='undefined'?window:this);
