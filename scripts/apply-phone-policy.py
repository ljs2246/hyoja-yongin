# 공식 근거 확인된 번호만 전화 연결 유지. 확인일 2026-10-30 (센터 7곳은 2026-10-26).
import re,glob,json,sys
D='2026-10-30'
Y='https://www.yongin.go.kr/'
SRC={
'119':('119 긴급신고(구급·구조)','https://www.mois.go.kr/frt/sub/a06/b10/emergencycall/screen.do'),
'112':('112 긴급신고(경찰)','https://www.mois.go.kr/frt/sub/a06/b10/emergencycall/screen.do'),
'129':('보건복지상담센터 129','https://www.mohw.go.kr/orgSearch.es?mid=a10604040000&org_cd=1352700'),
'1355':('국민연금 고객센터','https://www.nps.or.kr/pbcpgdnc/ognzprsn/getOHAG0021M0.do'),
'16003190':('에너지바우처 통합 상담센터','https://www.energyv.or.kr/'),
'16660420':('경기도 교통약자 광역이동지원센터','https://ggsts.gg.go.kr/'),
'15771122':('용인시 민원안내콜센터','https://www.yongin.go.kr/home/cvIf/cvIfTotal/cvIfTotal12.jsp'),
'03161932114':('용인시청 대표','https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1013&q_clCode=1&q_bbscttSn=20260331143713710'),
'03161932165':('용인시 문화예술과','https://www.yongin.go.kr/partInfo/cultureArt/BD_selectCultureArt.do?q_showIdx=16905&q_year=2026&q_month=10'),
'03161932462':('용인시 노인복지과','https://www.yongin.go.kr/home/www/www18/www18_02/www18_02_07.jsp'),
'03161932214':('용인시 노인복지과','https://www.yongin.go.kr/home/www/www18/www18_02/www18_02_03.jsp'),
'03161932466':('용인시 노인복지과 노인돌봄팀','https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1265&q_bbscttSn=20250828160000069'),
'03161933152':('용인시 장애인복지과','https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1001&q_bbscttSn=20260203093702620'),
'03161932067':('용인시 관광과','https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1013&q_clCode=1&q_bbscttSn=20260327153357010'),
'03161933336':('용인시 대중교통과','https://www.yongin.go.kr/user/bbs/BD_selectBbs.do?q_bbsCode=1020&q_bbscttSn=20260327101726830'),
'03161935114':('처인구청 대표','https://www.cheoingu.go.kr/'),
'03161930067':('처인구보건소(예방접종)','https://www.yongin.go.kr/home/www/www03/www03_03/www03_03_02/www03_03_02_02.jsp'),
'03161930316':('기흥구보건소(예방접종)','https://www.yongin.go.kr/home/www/www03/www03_03/www03_03_02/www03_03_02_02.jsp'),
'03161930805':('수지구보건소(예방접종)','https://www.yongin.go.kr/home/www/www03/www03_03/www03_03_02/www03_03_02_02.jsp'),
'03161930199':('처인구 치매안심센터','https://www.yongin.go.kr/home/health/healthSvc/imbcltyMng.jsp'),
'03161930408':('기흥구 치매안심센터','https://www.yongin.go.kr/home/health/healthSvc/imbcltyMng.jsp'),
'03161930883':('수지구 치매안심센터','https://www.yongin.go.kr/home/health/healthSvc/imbcltyMng.jsp'),
'03161930192':('처인구보건소 치매치료관리비','https://www.yongin.go.kr/home/health/healthSvc/imbcltyMng.jsp'),
'03161930415':('기흥구보건소 치매치료관리비','https://www.yongin.go.kr/home/health/healthSvc/imbcltyMng.jsp'),
'03161930888':('수지구보건소 치매치료관리비','https://www.yongin.go.kr/home/health/healthSvc/imbcltyMng.jsp'),
'0313000114':('강남병원 대표','https://www.knmc.or.kr/clin/clin6.php'),
'0313000119':('강남병원 응급의료센터','https://www.knmc.or.kr/clin/clin6.php'),
'03180212114':('다보스병원 대표','data/emergency.json (국립중앙의료원 공공데이터 2026-10-30)'),
'0313370114':('용인서울병원 대표','https://yishospital.com/?page_id=5240'),
'15510077':('메디필드한강병원 대표','https://www.gg.go.kr/contents/contents.do?ciIdx=987101&menuId=266061'),
'0313321119':('메디필드한강병원 응급실','https://www.gg.go.kr/contents/contents.do?ciIdx=987101&menuId=266061'),
'18991004':('용인세브란스병원 대표','https://yi.severance.healthcare/yi/patient-carer/guide/number.do'),
'0315188015':('용인세브란스병원 응급진료센터','https://yi.severance.healthcare/yi/patient-carer/guide/emergency.do'),
'0312018571':('백남준아트센터 관람문의','https://njp.ggcf.kr/'),
'0313360040':('용인자연휴양림','https://www.foresttrip.go.kr/rep/or/fcfsRsrvtMain.do?hmpgId=ID02030031&menuId=001001'),
'0313205000':('에버랜드 고객센터','https://www.everland.com/cscenter/faq-list'),
'0313260243':('용인시니어클럽','https://www.yongin.go.kr/home/job/yiJobInfo/oldJob.jsp'),
'0313249303':('용인시처인노인복지관','http://www.yiswc.or.kr/About_YISWC_08.php'),
'0313249305':('용인시처인노인복지관(031-324-9303~5)','http://www.yiswc.or.kr/About_YISWC_08.php'),
'0312848852':('용인시기흥노인복지관','https://www.ygsenior.or.kr/'),
'0313293500':('용인에버라인 대표','https://ever-line.co.kr/'),
'0315267755':('용인시 교통약자 이동지원센터(바우처택시)','https://www.yonginnuri.or.kr/'),
'07082110390':('다봄센터(고령 어르신 동행서비스)','http://www.yongin.go.kr/home/www/www18/www18_02/www18_02_06.jsp'),
}
CEN=json.load(open('docs/centers-recheck-open.json'))
for r in CEN['records']:
    if r['status']=='공식 원문 번호 일치':
        SRC[re.sub(r'\D','',r['displayPhone'])]=(r['name']+' 행정복지센터',r['sourceUrl'])
RE={'03151898511':('tel:18991004','대표 1899-1004','18991004'),'03151899001':('tel:0315188015','응급진료센터 031-5189-8015','0315188015')}
PAT=re.compile(r'<a ([^>]*?)href="tel:(\d+)"([^>]*)>(.*?)</a>',re.S)
EM='min-height:56px;box-sizing:border-box;display:flex;align-items:center;justify-content:space-between;gap:8px;border-radius:28px;background:#F3E6D6;color:#6A4A33;padding:8px 16px;font-size:17px;font-weight:700'
log=[]
for f in sorted(glob.glob('*.html')):
    s=open(f).read();o=s
    def rep(m):
        n=m.group(2);lab=re.sub(r'<[^>]+>','',m.group(4)).strip()
        if 'data-hj-blocked' in m.group(0):return m.group(0)
        if n in RE:
            t,l,k=RE[n];nm,u=SRC[k]
            log.append((f,n,lab,nm,u,D,'교체유지(공식 번호로 정정)'))
            return re.sub(r'href="tel:\d+"',f'data-hj-src="{u}" data-hj-checked="{D}" href="{t}"',m.group(0).replace(m.group(4),l),1)
        if n in SRC:
            nm,u=SRC[n]
            if 'data-hj-src' in m.group(0):
                log.append((f,n,lab,nm,u,CEN['checkedDate'],'유지'));return m.group(0)
            log.append((f,n,lab,nm,u,D,'유지'))
            return m.group(0).replace('<a ',f'<a data-hj-src="{u}" data-hj-checked="{D}" ',1)
        name=re.sub(r'[\d\-\s☎]+$','',lab).strip() or '기관'
        name=re.sub(r'\s*\d[\d\-]*$','',name)
        log.append((f,n,lab,name,None,D,'숨김'))
        return f'<div style="{EM}" data-hj-blocked="{name}"><span>{name}</span><span style="text-align:right;font-weight:500">전화번호 공식 확인 중</span></div>'
    s=PAT.sub(rep,s)
    if s!=o:open(f,'w').write(s)
json.dump([dict(zip(['page','number','label','agency','sourceUrl','checked','action'],r)) for r in log],open('docs/phone-policy-log.json','w'),ensure_ascii=False,indent=1)
print(len(log))
