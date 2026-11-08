#!/usr/bin/env python3
"""13개 화면 x 글자 3단계 터치 영역 44px 시험(갤럭시 화면 모의, 실기기 아님). 위반이 있으면 실패."""
import json,subprocess,sys,time,os
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));PORT=8131
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--directory',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
pages=['index','Emergency','All','Centers','Culture','Guide','Health','Jobs','Transit','Welfare','Ad','Ad2','Regions']
JS="""()=>{const out=[];const vis=e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,[role=button]').forEach(e=>{if(!vis(e))return;const r=e.getBoundingClientRect();
 // 본문 속 인라인 링크는 제외(문장 안 링크는 높이가 글줄 높이)
 const inline=e.tagName==='A'&&getComputedStyle(e).display==='inline'&&e.closest('p,li,td');if(inline)return;
 if(r.height<44||r.width<44)out.push([e.tagName,(e.innerText||e.getAttribute('aria-label')||e.id||'').trim().slice(0,24),Math.round(r.width),Math.round(r.height)])});return out}"""
res={}
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(**p.devices['Galaxy S9+']);pg=ctx.new_page()
    for fs in ['보통','크게','아주 크게']:
        for pn in pages:
            pg.goto(f'http://localhost:{PORT}/{pn}.html');pg.wait_for_timeout(500)
            try:
                if fs!='보통':pg.click(f'#sizeBtns button:has-text("{fs}")',timeout=1500);pg.wait_for_timeout(200)
            except Exception:pass
            v=pg.evaluate(JS);res[f'{pn}|{fs}']=v
    b.close()
srv.terminate()
tot=0
for k,v in res.items():
    if v:print(k,len(v),v[:4]);tot+=len(v)
print('총 위반(44px 미만) 요소:',tot,'/ 점검 조합',len(res))
json.dump({'기준':'터치 영역 44px 이상(본문 속 글줄 링크 제외)','기기':'Galaxy S9+ 화면 에뮬레이션(실기기 아님)','위반':{k:v for k,v in res.items() if v},'점검조합':len(res),'위반합계':tot},open(os.path.join(ROOT,'tests/touch-44-results.json'),'w'),ensure_ascii=False,indent=1)
sys.exit(1 if tot else 0)
