#!/usr/bin/env python3
"""글자 크기 3단계에서 첫 화면 제목이 낱말 중간에서 끊기지 않고 글자 크기 버튼이 한 줄인지 시험(갤럭시 S25+ 폭 412, 작은 폭 360 모의)."""
import json,subprocess,sys,time,os
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));PORT=8133
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--directory',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
R=[]
def rec(n,ok):R.append((n,bool(ok)));print(('통과 ' if ok else '실패 ')+n)
JS="""()=>{const e=document.querySelector('#family-title');const words=['사랑하는','마음,','언제나','곁에.'];
const t=e.firstChild.textContent+'|'+e.lastChild.textContent;const r=document.createRange();let broken=[];
for(const node of [e.firstChild,e.lastChild]){const txt=node.textContent;let i=0;for(const w of txt.split(/\\s+/)){const s=txt.indexOf(w,i);if(!w){continue}i=s+w.length;
 const rg=document.createRange();rg.setStart(node,s);rg.setEnd(node,s+w.length);const tops=new Set([...rg.getClientRects()].map(x=>Math.round(x.top)));if(tops.size>1)broken.push(w)}}
return broken}"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for w,name in [(412,'S25+ 폭 412'),(360,'작은 폭 360')]:
        c=b.new_context(viewport={'width':w,'height':900},is_mobile=True,has_touch=True);pg=c.new_page()
        pg.goto(f'http://localhost:{PORT}/index.html');pg.wait_for_timeout(700)
        for sz in ['보통','크게','아주 크게']:
            pg.click(f'#sizeBtns button:has-text("{sz}")');pg.wait_for_timeout(300)
            rec(f'{name} · {sz}: 제목 낱말이 중간에서 끊기지 않음',pg.evaluate(JS)==[])
            one=pg.evaluate("()=>[...document.querySelectorAll('#sizeBtns button')].every(b=>{const r=document.createRange();r.selectNodeContents(b);return new Set([...r.getClientRects()].map(x=>Math.round(x.top))).size===1})")
            rec(f'{name} · {sz}: 글자 크기 버튼이 모두 한 줄',one)
            rec(f'{name} · {sz}: 가로 스크롤 없음',not pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth"))
    b.close()
srv.terminate()
f=sum(1 for _,o in R if not o)
json.dump({'통과':len(R)-f,'실패':f,'항목':[{'이름':n,'결과':'통과' if o else '실패'} for n,o in R],'비고':'모의 브라우저(실기기 아님)'},open(os.path.join(ROOT,'tests/wordbreak-results.json'),'w'),ensure_ascii=False,indent=1)
print(f'줄바꿈 시험: 통과 {len(R)-f} / 실패 {f}');sys.exit(1 if f else 0)
