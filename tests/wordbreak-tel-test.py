#!/usr/bin/env python3
"""약국·병원 화면: 전화번호가 한 줄, 지도 버튼 낱말이 중간에서 끊기지 않는지 시험(폭 412·360, 글자 3단계, 모의 브라우저)."""
import json,subprocess,sys,time,os
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));PORT=8134
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--directory',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
R=[]
def rec(n,ok):R.append((n,bool(ok)));print(('통과 ' if ok else '실패 ')+n)
SPLIT="""()=>{let bad=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
while(n=w.nextNode()){const p=n.parentElement;if(!p||/SCRIPT|STYLE/.test(p.tagName)||!p.closest('.hj-medical-maps a,a[href^="tel:"]'))continue;
const t=n.textContent;let i=0;for(const x of t.split(/\\s+/)){if(!x)continue;const s=t.indexOf(x,i);i=s+x.length;const r=document.createRange();r.setStart(n,s);r.setEnd(n,s+x.length);
if(new Set([...r.getClientRects()].map(q=>Math.round(q.top))).size>1&&!/^[0-9\\-~]+$/.test(x))bad.push(x)}}return bad}"""
TELSPLIT="""()=>[...document.querySelectorAll('a[href^="tel:"] .tn')].filter(e=>{const r=document.createRange();r.selectNodeContents(e);return new Set([...r.getClientRects()].map(q=>Math.round(q.top))).size>1}).map(e=>e.textContent)"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for w,name in [(412,'폭 412'),(360,'폭 360')]:
        c=b.new_context(viewport={'width':w,'height':900},is_mobile=True,has_touch=True);pg=c.new_page()
        pg.goto(f'http://localhost:{PORT}/Emergency.html');pg.wait_for_timeout(1500)
        # 나중에 그려지는 전화 버튼(약국 목록 방식) 모사
        pg.evaluate("()=>{const a=document.createElement('a');a.href='tel:0312637128';a.textContent='전화 031-263-7128';a.style.cssText='display:flex;min-height:56px';document.body.appendChild(a)}");pg.wait_for_timeout(300)
        for sz in ['보통','크게','아주 크게']:
            try:pg.click(f'#sizeBtns button:has-text("{sz}")',timeout=2000)
            except Exception:
                pg.goto(f'http://localhost:{PORT}/index.html');pg.wait_for_timeout(500);pg.click(f'#sizeBtns button:has-text("{sz}")');pg.goto(f'http://localhost:{PORT}/Emergency.html');pg.wait_for_timeout(1200)
                pg.evaluate("()=>{const a=document.createElement('a');a.href='tel:0312637128';a.textContent='전화 031-263-7128';a.style.cssText='display:flex;min-height:56px';document.body.appendChild(a)}");pg.wait_for_timeout(300)
            pg.wait_for_timeout(300)
            rec(f'{name} · {sz}: 전화번호가 한 줄',pg.evaluate(TELSPLIT)==[])
            rec(f'{name} · {sz}: 지도·전화 버튼 낱말이 중간에서 끊기지 않음',pg.evaluate(SPLIT)==[])
            rec(f'{name} · {sz}: 가로 스크롤 없음',not pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth"))
    b.close()
srv.terminate()
f=sum(1 for _,o in R if not o)
json.dump({'통과':len(R)-f,'실패':f,'항목':[{'이름':n,'결과':'통과' if o else '실패'} for n,o in R],'비고':'모의 브라우저(실기기 아님)'},open(os.path.join(ROOT,'tests/wordbreak-tel-results.json'),'w'),ensure_ascii=False,indent=1)
print(f'전화·지도 줄바꿈 시험: 통과 {len(R)-f} / 실패 {f}');sys.exit(1 if f else 0)
