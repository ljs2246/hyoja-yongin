#!/usr/bin/env python3
"""일반 병원·의원 공식 자료 → 격리 보관(고객 화면 노출 금지). 심평원 병원정보서비스 getHospBasisList(항목명은 가정, 공식 명세 확인 전 미검증).
- 인증키는 환경변수 DATA_GO_KR_KEY 로만 받음(코드·저장소에 두지 않음). 예약 실행 없음, 수동 실행 전용.
- 결과는 data/staging/hospitals-pending.json 에만 저장(상태=격리 대기). 어떤 화면·서비스워커도 이 파일을 읽지 않음(check-staging.py 로 검사).
사용: fetch_hospitals.py --parse <xml파일> [--out 경로]   |   fetch_hospitals.py (키가 있을 때 공식 API 호출)"""
import sys,re,json,os,argparse,xml.etree.ElementTree as ET
URL='https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList'
PH=re.compile(r'^0(2|[3-6][1-5])-\d{3,4}-\d{4}$')
def parse(xml):
    items=[];root=ET.fromstring(xml)
    for it in root.iter('item'):
        g=lambda k:(it.findtext(k) or '').strip()
        items.append({'이름':g('yadmNm'),'주소':g('addr'),'전화':g('telno'),'종별':g('clCdNm'),'시도':g('sidoCdNm'),'시군구':g('sgguCdNm'),'기관기호':g('ykiho')})
    return items
def screen(items):
    ok=[];rej=[];seen=set()
    for x in items:
        why=[]
        if '용인' not in x['시군구'] and '용인시' not in x['주소']:why.append('용인 아님')
        if not x['이름'] or not x['주소']:why.append('필수항목 누락')
        if not PH.match(x['전화']):why.append('전화번호 형식 이상')
        k=x['기관기호'] or (x['이름'],x['주소'])
        if not why and k in seen:why.append('중복')
        if why:rej.append({**x,'제외사유':why});continue
        seen.add(k);ok.append({**x,'상태':'격리 대기','검증':'미검증(공식 원문·전화 대조 전)'})
    return ok,rej
def main():
    a=argparse.ArgumentParser();a.add_argument('--parse');a.add_argument('--out',default='data/staging/hospitals-pending.json');a=a.parse_args()
    if a.parse:xml=open(a.parse,encoding='utf-8').read()
    else:
        key=os.environ.get('DATA_GO_KR_KEY')
        if not key:print('인증키(DATA_GO_KR_KEY) 없음 → 호출하지 않음(공공데이터포털 활용신청 필요)');return 2
        import urllib.request,urllib.parse
        q=urllib.parse.urlencode({'serviceKey':key,'sidoCd':'410000','sgguCd':'','numOfRows':1000,'pageNo':1})
        xml=urllib.request.urlopen(URL+'?'+q,timeout=30).read().decode('utf-8')
    ok,rej=screen(parse(xml))
    os.makedirs(os.path.dirname(a.out),exist_ok=True)
    json.dump({'상태':'격리 대기(고객 화면 노출 금지)','출처':URL,'항목명':'가정(공식 명세 확인 전)','통과건수':len(ok),'제외건수':len(rej),'목록':ok,'제외':rej},open(a.out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(f'격리 보관 {a.out}: 통과 {len(ok)} / 제외 {len(rej)}');return 0
if __name__=='__main__':sys.exit(main())
