# 모든 화면 버튼마다 🔊(소리 듣기) 붙었는지, 글자 크기 3단계·폭 4종에서 좌우 넘침/작은 버튼이 없는지 검사 (실패 시 종료코드 1)
import sys
from playwright.sync_api import sync_playwright
import http.server,socketserver,threading,functools
H=functools.partial(http.server.SimpleHTTPRequestHandler,directory=__import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__))));H.log_message=lambda *a:None
s=socketserver.TCPServer(('127.0.0.1',0),H);port=s.server_address[1];threading.Thread(target=s.serve_forever,daemon=True).start()
JS="""()=>{const SK='[data-hjnav],[data-hjfoot],#hj-readbar,#hj-sizebar,#hj-sndbar,#sizeBtns,#hj-share-x,#hj-kakao,footer,header,.home-nav,details.home-sound-settings,form,[role=tablist]';
const tg=[...document.querySelectorAll('a[href],button')].filter(e=>{if(e.closest(SK)||e.classList.contains('hj-say2')||e.classList.contains('hj-say')||e.disabled)return false;const h=e.getAttribute('href')||'';if(e.tagName==='A'&&(h[0]==='#'||h==='index.html'||h===''))return false;return (e.textContent||'').trim()&&getComputedStyle(e).display!=='none'});
const unc=tg.filter(e=>!e.closest('.hj-tw2,.hj-tw')&&!(e.parentNode.getAttribute&&e.parentNode.getAttribute('data-hjmap')&&document.querySelectorAll('.hj-pair').length>=2)).map(e=>e.textContent.trim().slice(0,20));
const de=document.documentElement;const sm=[...document.querySelectorAll('.hj-say2')].filter(b=>{const r=b.getBoundingClientRect();return r.width&&(r.width<44||r.height<44)}).length;
const orphan=[...document.querySelectorAll('.hj-tw2:not(.hj-pair)')].filter(w=>!w.querySelector('a,button:not(.hj-say2)')).length;
return [tg.length,document.querySelectorAll('.hj-say2').length,unc.length,unc.slice(0,3),de.scrollWidth>de.clientWidth+1,sm,orphan]}"""
bad=0;rows=[]
with sync_playwright() as p:
    b=p.chromium.launch()
    for w in (320,360,390,412):
      for z in ('normal','large','xl'):
        c=b.new_context(viewport={'width':w,'height':844},is_mobile=True,has_touch=True)
        for n in ['index','Emergency','Health','Welfare','Transit','Culture','Jobs','Guide','All','Centers','Regions','Ad','Ad2']:
            pg=c.new_page();pg.route('**/*open-meteo*',lambda r:r.abort());pg.goto(f'http://127.0.0.1:{port}/{n}.html');pg.wait_for_timeout(1300)
            if z!='normal':
                try:pg.evaluate("(i)=>{const b=document.querySelectorAll('#sizeBtns button,#hj-sizebar button');b[i]&&b[i].click()}",1 if z=='large' else 2);pg.wait_for_timeout(1100)
                except Exception:pass
            r=pg.evaluate(JS)
            if w==390 and z=='normal':pg.screenshot(path=f'/tmp/say_{n}_390.png',full_page=(n in('Health','Welfare')))
            ok=not(r[2]>0 or r[4] or r[5] or r[6]); bad+=0 if ok else 1; rows.append((w,z,n,r[0],r[1],ok))
            if not ok:print('X',w,z,n,r)
            pg.close()
print('cases',len(rows),'bad',bad)
for n in ['index','Emergency','Health','Welfare','Transit','Culture','Jobs','Guide','All','Centers','Regions','Ad','Ad2']:
    r=[x for x in rows if x[2]==n and x[0]==390 and x[1]=='normal'][0];print(n,r[3],r[4])
sys.exit(1 if bad else 0)
