#!/usr/bin/env python3
"""13개 화면 점검: 글자 3단계 x 폭 412/360. 가로 넘침, 낱말 중간 끊김, 누르는 곳 44px 미만, 겹침을 센다(모의 브라우저)."""
import json,subprocess,sys,time,os,glob
from playwright.sync_api import sync_playwright
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'));PORT=8139
srv=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),'--directory',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
PAGES=['index','Emergency','Health','Welfare','Transit','Culture','Jobs','Centers','All','Regions','Guide','Ad','Ad2','Review']
JS="""()=>{const W=document.documentElement.clientWidth;const out={over:document.documentElement.scrollWidth-W,split:[],small:[],clip:[]};
const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;
while(n=w.nextNode()){const p=n.parentElement;if(!p||/SCRIPT|STYLE|NOSCRIPT/.test(p.tagName)||p.offsetParent===null)continue;const t=n.textContent;let i=0;
 for(const x of t.split(/\\s+/)){if(!x)continue;const s=t.indexOf(x,i);i=s+x.length;if(x.length<2)continue;const r=document.createRange();r.setStart(n,s);r.setEnd(n,s+x.length);
  if(new Set([...r.getClientRects()].map(q=>Math.round(q.top))).size>1&&/[가-힣]{2}/.test(x)&&!/^\\d/.test(x))out.split.push(x.slice(0,12))}}
for(const e of document.querySelectorAll('a,button,select,input,summary')){if(e.offsetParent===null)continue;const r=e.getBoundingClientRect();if(r.width===0)continue;
 if(r.height<44||r.width<44)out.small.push((e.textContent||e.getAttribute('aria-label')||e.tagName).trim().slice(0,12)+' '+Math.round(r.width)+'x'+Math.round(r.height));
 if(r.right>W+1)out.clip.push((e.textContent||'').trim().slice(0,12))}
return out}"""
res={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for w in (412,360):
        c=b.new_context(viewport={'width':w,'height':900},is_mobile=True,has_touch=True);pg=c.new_page()
        for sz in ['보통','크게','아주 크게']:
            pg.goto(f'http://localhost:{PORT}/index.html');pg.wait_for_timeout(500)
            pg.click(f'#sizeBtns button:has-text("{sz}")');pg.wait_for_timeout(200)
            for n in PAGES:
                if not os.path.exists(os.path.join(ROOT,n+'.html')):continue
                pg.goto(f'http://localhost:{PORT}/{n}.html');pg.wait_for_timeout(900)
                r=pg.evaluate(JS);res[f'{n}|{w}|{sz}']=r
    b.close()
srv.terminate()
json.dump(res,open('/tmp/audit.json','w'),ensure_ascii=False)
agg={}
for k,v in res.items():
    n=k.split('|')[0];a=agg.setdefault(n,{'넘침':0,'끊김':set(),'작은버튼':set(),'잘림':set()})
    if v['over']>0:a['넘침']+=1
    a['끊김']|=set(v['split']);a['작은버튼']|=set(v['small']);a['잘림']|=set(v['clip'])
for n,a in agg.items():print(n,'넘침',a['넘침'],'/6 끊김',len(a['끊김']),list(a['끊김'])[:4],'작은버튼',len(a['작은버튼']),list(a['작은버튼'])[:3],'잘림',len(a['잘림']))
bad=[n for n,a in agg.items() if a['넘침'] or a['잘림']]
json.dump({n:{'가로넘침_횟수(6중)':a['넘침'],'끊김_낱말수':len(a['끊김']),'작은버튼수':len(a['작은버튼']),'잘림':len(a['잘림'])} for n,a in agg.items()},open(os.path.join(ROOT,'tests/screen-audit-results.json'),'w'),ensure_ascii=False,indent=1)
print('화면 넘침·잘림 없음' if not bad else '넘침·잘림 화면: '+','.join(bad));sys.exit(1 if bad else 0)
