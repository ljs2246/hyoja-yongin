#!/usr/bin/env python3
"""대표 결정(2026-11-06): 강남병원 응급실 0119와 미확인 약국 번호가 어느 화면에도 보이지 않는지 시험(모의 브라우저)."""
import json,subprocess,sys,time,os
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));PORT=8137
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--directory',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
R=[]
def rec(n,ok):R.append((n,bool(ok)));print(('통과 ' if ok else '실패 ')+n)
PAGES=['index','Emergency','Health','Welfare','Transit','Culture','Jobs','Centers','All']
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_context(viewport={'width':412,'height':900}).new_page()
    for n in PAGES:
        pg.goto(f'http://localhost:{PORT}/{n}.html');pg.wait_for_timeout(1200)
        t=pg.inner_text('body');h=pg.evaluate("[...document.querySelectorAll('a[href^=\"tel:\"]')].map(a=>a.getAttribute('href'))")
        rec(f'{n}: 강남병원 응급실 0119 글자·링크 없음','300-0119' not in t and 'tel:0313000119' not in ''.join(h) and '0313000119' not in h)
    pg.goto(f'http://localhost:{PORT}/Emergency.html');pg.wait_for_timeout(1500)
    base=pg.evaluate("document.querySelectorAll('a[href^=\"tel:\"]').length")
    pg.select_option('#medicalKind','pharmacy');pg.wait_for_timeout(1200)
    for gu in ['처인구','기흥구','수지구']:
        pg.select_option('#medicalGu',gu);pg.wait_for_timeout(1500)
        cards=pg.evaluate("document.querySelectorAll('.hj-medical-maps').length")
        tels=pg.evaluate("document.querySelectorAll('a[href^=\"tel:\"]').length")
        rec(f'약국 {gu}: 약국 목록이 실제로 그려짐(카드 {cards}개)',cards>0)
        rec(f'약국 {gu}: 미확인 약국 전화 버튼 없음(전화 링크 {base}→{tels})',tels<=base)
    b.close()
srv.terminate()
f=sum(1 for _,o in R if not o)
json.dump({'통과':len(R)-f,'실패':f,'항목':[{'이름':n,'결과':'통과' if o else '실패'} for n,o in R],'비고':'모의 브라우저(실기기 아님)'},open(os.path.join(ROOT,'tests/phone-hide-results.json'),'w'),ensure_ascii=False,indent=1)
print(f'번호 숨김 시험: 통과 {len(R)-f} / 실패 {f}');sys.exit(1 if f else 0)
