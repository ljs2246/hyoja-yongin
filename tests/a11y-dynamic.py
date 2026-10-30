# 광고 화면·전체 메뉴 포함 13개 화면 접근성 동적 검사 (Chromium 모의, 360px). 결과: tests/a11y-dynamic-results.json
# 실행: python3 tests/a11y-dynamic.py [--report]   (--report: 실패해도 종료코드 0, 발견 사항만 출력)
import subprocess,time,json,sys
from playwright.sync_api import sync_playwright
PORT=8794;REPORT='--report' in sys.argv
PAGES=['index','Emergency','Welfare','Transit','All','Culture','Health','Jobs','Centers','Guide','Regions','Ad','Ad2']
srv=subprocess.Popen(['python3','-m','http.server',str(PORT)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
JS=r"""()=>{
 const out={};const vis=e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'};
 const name=e=>(e.getAttribute('aria-label')||e.textContent||e.getAttribute('title')||[...e.querySelectorAll('img')].map(i=>i.alt).join('')||'').trim();
 out.lang=document.documentElement.lang;out.h1=[...document.querySelectorAll('h1')].length;
 const hs=[...document.querySelectorAll('h1,h2,h3,h4')].filter(vis).map(h=>+h.tagName[1]);let skip=false;for(let i=1;i<hs.length;i++)if(hs[i]-hs[i-1]>1)skip=true;out.headSkip=skip;
 out.landmark=!!document.querySelector('main,[role=main]');out.skip=!!document.querySelector('a.home-skip,a[href^="#main"]');
 out.noName=[...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea')].filter(vis).filter(e=>!(name(e)||(e.id&&document.querySelector('label[for="'+e.id+'"]')))).map(e=>(e.outerHTML||'').slice(0,70));
 out.noAlt=[...document.querySelectorAll('img')].filter(i=>!i.hasAttribute('alt')).map(i=>i.src.slice(-30));
 const ids={};out.dupId=[];document.querySelectorAll('[id]').forEach(e=>{if(ids[e.id])out.dupId.push(e.id);ids[e.id]=1});
 out.small=[...document.querySelectorAll('a[href],button,select,input:not([type=hidden])')].filter(vis).filter(e=>{const r=e.getBoundingClientRect();const inline=getComputedStyle(e).display==='inline'&&e.closest('p,li,div[style*="line-height"],span');return r.height<44&&!inline}).map(e=>name(e).slice(0,18)+'|'+Math.round(e.getBoundingClientRect().height));
 const lum=c=>{const a=c.map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*a[0]+.7152*a[1]+.0722*a[2]};
 const rgb=s=>{const m=s.match(/[\d.]+/g);return m?m.map(Number):null};
 const bgs=e=>{while(e){const cs=getComputedStyle(e);const bi=cs.backgroundImage;if(bi&&bi!=='none'){const m=[...bi.matchAll(/rgba?\([^)]+\)/g)].map(x=>rgb(x[0]).slice(0,3));if(m.length)return m}const c=rgb(cs.backgroundColor);if(c&&(c.length<4||c[3]>0.95))return [c.slice(0,3)];e=e.parentElement}return [[255,255,255]]};
 out.lowContrast=[];const seen=new Set();
 document.querySelectorAll('main *, .hj-page *, body > *').forEach(e=>{if(!vis(e)||!e.childNodes.length)return;const t=[...e.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).map(n=>n.textContent.trim()).join('');if(!t)return;
  const s=getComputedStyle(e);const f=rgb(s.color);if(!f)return;const L1=lum(f.slice(0,3));const cr=Math.min(...bgs(e).map(b=>{const L2=lum(b);return (Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05)}));const px=parseFloat(s.fontSize),bold=+s.fontWeight>=700;const large=px>=24||(px>=18.66&&bold);
  if(cr<(large?3:4.5)){const k=t.slice(0,20)+cr.toFixed(1);if(!seen.has(k)){seen.add(k);out.lowContrast.push(t.slice(0,22)+' '+cr.toFixed(2)+':1 '+px+'px')}}});
 out.minFont=Math.min(...[...document.querySelectorAll('main *, .hj-page *')].filter(vis).filter(e=>[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim())).map(e=>parseFloat(getComputedStyle(e).fontSize)));
 out.extBlank=[...document.querySelectorAll('a[href^="http"]')].filter(a=>a.target==='_blank'&&!/noopener/.test(a.rel)).length;
 out.adLabel=/광고/.test(document.body.innerText);
 return out}"""
R=[];F=[]
try:
  with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True);pg=ctx.new_page()
    pg.route('**/fonts.googleapis.com/**',lambda r:r.abort());pg.route('**/api.open-meteo.com/**',lambda r:r.abort())
    for n in PAGES:
        pg.goto(f'http://localhost:{PORT}/{n}.html');pg.wait_for_timeout(500);o=pg.evaluate(JS);o['page']=n
        # 키보드: Tab 8번 후 포커스 윤곽선
        pg.keyboard.press('Tab');pg.keyboard.press('Tab');ol=pg.evaluate("(()=>{const e=document.activeElement;if(!e||e===document.body)return 'none';const s=getComputedStyle(e);return (s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>=2)||s.boxShadow!=='none'?'ok':'no-outline'})()")
        o['focus']=ol;R.append(o)
        iss=[]
        if o['lang']!='ko':iss.append('lang')
        if o['h1']!=1:iss.append(f"h1 {o['h1']}개")
        if o['headSkip']:iss.append('제목 단계 건너뜀')
        if not o['landmark']:iss.append('main 영역 없음')
        if o['noName']:iss.append('이름 없는 조작요소 '+str(o['noName'][:2]))
        if o['noAlt']:iss.append('alt 없는 이미지')
        if o['dupId']:iss.append('중복 id '+str(o['dupId']))
        if o['small']:iss.append(f"44px 미만 조작요소 {len(o['small'])}개 "+str(o['small'][:3]))
        if o['lowContrast']:iss.append('대비 부족 '+str(o['lowContrast'][:3]))
        if o['minFont']<16:iss.append(f"최소 글자 {o['minFont']}px")
        if o['focus']!='ok':iss.append('포커스 표시 '+o['focus'])
        if o['extBlank']:iss.append('새 탭 링크 noopener 없음')
        if n in('Ad','Ad2') and not o['adLabel']:iss.append('광고 표시 없음')
        F.append((n,iss));print(('통과' if not iss else '발견'),n,'; '.join(iss))
    b.close()
finally:srv.terminate()
json.dump({'pages':R,'issues':{n:i for n,i in F}},open('tests/a11y-dynamic-results.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
bad=sum(1 for _,i in F if i);print(f'\n페이지 {len(F)}개 중 발견 {bad}개');sys.exit(0 if (REPORT or not bad) else 1)
