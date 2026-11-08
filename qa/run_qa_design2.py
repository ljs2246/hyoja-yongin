#!/usr/bin/env python3
"""효자 2차 디자인 전용 검수 (모의 휴대폰 브라우저).
첫 화면·가족에게 보내기·하단 홈/메뉴/가족 이동·가족 전화 저장·지역 저장·소리 읽기·버튼 크기·글자 3단계.
결과 구분: PASS(통과) / FAIL(실패) / WARN(경고) / DEVICE(실기기 확인 필요). 임의로 통과 처리하지 않는다.
사용: python3 qa/run_qa_design2.py [--root .] [--out qa-report-design2]
"""
import argparse, functools, http.server, io, json, os, re, socketserver, sys, threading, datetime
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--out', default='qa-report-design2')
a = ap.parse_args()
ROOT = os.path.abspath(a.root); OUT = os.path.abspath(a.out)
os.makedirs(OUT + '/screenshots', exist_ok=True)

H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
H.log_message = lambda *x: None
srv = socketserver.TCPServer(('127.0.0.1', 0), H)
U = f'http://127.0.0.1:{srv.server_address[1]}/'
threading.Thread(target=srv.serve_forever, daemon=True).start()

R = []
def rec(group, name, status, detail='', shot=None):
    R.append(dict(group=group, name=name, status=status, detail=detail, shot=shot))
    mark = {'PASS': '통과', 'FAIL': '실패', 'WARN': '경고', 'DEVICE': '실기기 확인 필요'}[status]
    print(f'[{mark}] {group} · {name}' + (f' · {detail}' if detail else ''))

def shot(pg, name):
    p = re.sub(r'[^0-9A-Za-z가-힣_.-]+', '_', name) + '.png'
    try: pg.screenshot(path=f'{OUT}/screenshots/{p}', full_page=True)
    except Exception: return None
    return 'screenshots/' + p

NOPREVENT = "document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[href^=\"tel:\"],a[href^=\"sms:\"],a[href^=\"intent:\"]');if(a)e.preventDefault();},true)"
SPEECH = """
window.__sp={speak:[],cancel:0};
const fake={speak(u){window.__sp.speak.push(u.text);},cancel(){window.__sp.cancel++;},getVoices(){return [];},addEventListener(){},removeEventListener(){},speaking:false,pending:false};
Object.defineProperty(window,'speechSynthesis',{value:fake,configurable:true});
window.SpeechSynthesisUtterance=function(t){this.text=t;};
"""

def new_ctx(b, w=390, h=844, extra=''):
    ctx = b.new_context(viewport={'width': w, 'height': h}, is_mobile=True, has_touch=True, device_scale_factor=1)
    pg = ctx.new_page()
    reqs = []
    ctx.on('request', lambda r: reqs.append((r.url, r.post_data or '')) if not r.url.startswith(U) and not r.url.startswith('data:') else None)
    pg.route(re.compile(r'.*open-meteo.*'), lambda r: r.abort())
    pg.route(re.compile(r'https://map\.(naver|kakao)\.com/.*'), lambda r: r.abort())
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
    ctx.add_init_script(SPEECH + extra)
    return ctx, pg, reqs, errs

def tap(pg, sel):
    el = pg.locator(sel).first
    el.evaluate("e=>e.scrollIntoView({block:'center',behavior:'instant'})"); pg.wait_for_timeout(450)
    hit = el.evaluate("e=>{const b=e.getBoundingClientRect();const t=document.elementFromPoint(b.left+b.width/2,b.top+b.height/2);return t===e||e.contains(t)?'':(t?t.tagName+':'+(t.textContent||'').slice(0,30):'none')}")
    if hit: raise RuntimeError(f'{sel} 이(가) {hit} 에 가려 눌리지 않음')
    bb = el.bounding_box(); pg.mouse.click(bb['x'] + bb['width'] / 2, bb['y'] + bb['height'] / 2)

def jpeg_bytes():
    from PIL import Image
    im = Image.new('RGB', (300, 220), (200, 120, 90)); buf = io.BytesIO(); im.save(buf, 'JPEG'); return buf.getvalue()

NAME, PHONE_IN, PHONE_D = '큰딸', '010-1234-5678', '01012345678'   # 가짜 시험 값

with sync_playwright() as p:
    b = p.chromium.launch()

    # ── A. 첫 화면 ──
    ctx, pg, reqs, errs = new_ctx(b)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1500); pg.evaluate(NOPREVENT)
    g = 'A 첫 화면'
    txt = pg.evaluate('document.body.innerText')
    for need in ['오늘, 마음을 전해요', '급할 때', '문화·나들이', '건강교실', '일자리', '복지·혜택', '이동·교통', '전체 보기', '가족에게 전화']:
        rec(g, f'문구 "{need}" 보임', 'PASS' if need in txt else 'FAIL', '' if need in txt else '화면에 없음', None if need in txt else shot(pg, 'A_missing_' + need))
    sh = pg.evaluate("(()=>{const b=document.getElementById('hj-kakao');if(!b)return null;const r=b.getBoundingClientRect();const cs=getComputedStyle(b);return {label:(b.textContent||'').trim()+'|'+(getComputedStyle(b,'::after').content||''),w:Math.round(r.width),h:Math.round(r.height),vis:r.width>0&&cs.visibility!=='hidden'}})()")
    rec(g, '가족에게 보내기(공유) 버튼이 보임', 'PASS' if sh and sh['vis'] and sh['h']>=44 else 'FAIL', str(sh))
    urg = pg.evaluate("(()=>{const a=document.querySelector('a.hj-urgent');return a?a.getAttribute('href'):null})()")
    rec(g, '급할 때 버튼 → Emergency.html', 'PASS' if urg == 'Emergency.html' else 'FAIL', f'href={urg}')
    tiles = pg.evaluate("[...document.querySelectorAll('a.hj-tile')].map(a=>[a.textContent.trim().slice(0,12),a.getAttribute('href')])")
    rec(g, '메뉴 6칸 링크', 'PASS' if len(tiles) >= 5 else 'FAIL', f'{len(tiles)}개 {tiles}')
    rec(g, '스크립트 오류 없음', 'PASS' if not errs else 'FAIL', '; '.join(errs))
    ext = sorted({re.sub(r'^(https?://[^/]+).*', r'\1', u) for u, _ in reqs})
    rec(g, '자동 외부 접속 없음(날씨 제외)', 'PASS' if not [e for e in ext if 'open-meteo' not in e] else 'FAIL', str(ext))
    shot(pg, 'A_home_390')

    # 가족에게 보내기
    g = 'B 가족에게 보내기'
    pg.evaluate("window.__cb=[];Object.defineProperty(navigator,'clipboard',{value:{writeText:t=>{window.__cb.push(t);return Promise.resolve();}},configurable:true});Object.defineProperty(navigator,'share',{value:undefined,configurable:true})")
    try:
        tap(pg, '#hj-kakao'); pg.wait_for_timeout(400)
        cb = pg.evaluate('window.__cb'); msg = pg.evaluate("(document.getElementById('hj-share-msg')||{}).innerText||''")
        rec(g, '버튼을 누르면 주소 복사 + 안내 문구', 'PASS' if cb and msg else 'FAIL', f'복사={cb} 안내="{msg[:40]}"')
        rec(g, '복사된 값은 화면 주소만(개인 정보 없음)', 'PASS' if cb and cb[0].startswith(U) and '010' not in cb[0] and NAME not in cb[0] else 'FAIL', str(cb))
        sms = pg.evaluate("[...document.querySelectorAll('#hj-share-x a')].map(a=>a.getAttribute('href').slice(0,40))")
        rec(g, '문자로 보내기 링크(주소만 담김)', 'PASS' if any(s.startswith('sms:?body=') for s in sms) else 'FAIL', str(sms))
    except Exception as e:
        rec(g, '가족에게 보내기 동작', 'FAIL', str(e)[:150], shot(pg, 'B_share_fail'))
    rec(g, '실제 카카오톡·문자 앱으로 넘어가는지', 'DEVICE', '모의 브라우저로는 앱 전환을 볼 수 없어요. 갤럭시에서 확인')
    ctx.close()

    # ── C. 하단 홈·메뉴·가족 ──
    g = 'C 하단 이동'
    ctx, pg, reqs, errs = new_ctx(b)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1500)
    nav = pg.evaluate("[...document.querySelectorAll('.home-nav a')].map(a=>[a.textContent.trim(),a.getAttribute('href')])")
    labels = [n[0] for n in nav]
    rec(g, '하단 3칸(홈·메뉴·가족)', 'PASS' if len(nav) == 3 and any('홈' in l for l in labels) and any('메뉴' in l for l in labels) and any('가족' in l for l in labels) else 'FAIL', str(nav))
    sticky = pg.evaluate("(()=>{const n=document.querySelector('.home-nav');const r=n.getBoundingClientRect();return [getComputedStyle(n).position,Math.round(r.bottom),innerHeight]})()")
    rec(g, '하단 메뉴가 화면 아래에 붙어 있음', 'PASS' if sticky[1] >= sticky[2] - 2 else 'WARN', str(sticky))
    for lab, expect in (('메뉴', 'All.html'), ('가족', '#family'), ('홈', 'index.html')):
        try:
            pg.goto(U + 'index.html'); pg.wait_for_timeout(900)
            tap(pg, f'.home-nav a:has-text("{lab}")'); pg.wait_for_timeout(700)
            url = pg.url
            ok = expect in url
            if lab == '가족':
                vis = pg.evaluate("(()=>{const e=document.getElementById('hjFamily');const r=e.getBoundingClientRect();return r.top<innerHeight&&r.bottom>0})()")
                ok = ok and vis
            rec(g, f'{lab} 누르면 이동', 'PASS' if ok else 'FAIL', url.replace(U, ''), None if ok else shot(pg, 'C_nav_' + lab))
        except Exception as e:
            rec(g, f'{lab} 누르면 이동', 'FAIL', str(e)[:150], shot(pg, 'C_nav_err_' + lab))
    # 다른 화면에서도 하단 메뉴가 있고 마지막 내용을 가리지 않는지
    bad = []
    for n in ['All', 'Emergency', 'Centers', 'Culture', 'Guide', 'Health', 'Jobs', 'Transit', 'Welfare']:
        pg.goto(U + f'{n}.html'); pg.wait_for_timeout(900)
        r = pg.evaluate("(()=>{const nav=document.querySelector('.home-nav');if(!nav)return 'nav없음';window.scrollTo(0,document.documentElement.scrollHeight);const nb=nav.getBoundingClientRect();const x=[...document.querySelectorAll('a,button,input,select')].filter(e=>e.offsetParent&&!nav.contains(e)&&!e.closest('[data-hjnav]')).filter(e=>{const b=e.getBoundingClientRect();return b.height>0&&b.bottom>nb.top+2&&b.top<nb.bottom-2});return x.length?('가려짐 '+x.length+'개'):''})()")
        if r: bad.append(f'{n}:{r}')
    rec(g, '9개 화면 맨 아래에서 하단 메뉴가 버튼을 가리지 않음', 'PASS' if not bad else 'FAIL', '; '.join(bad))
    ctx.close()

    # ── D. 가족 전화 저장 ──
    g = 'D 가족 전화'
    ctx, pg, reqs, errs = new_ctx(b)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1500); pg.evaluate(NOPREVENT)
    def fam_state(): return pg.evaluate("(()=>{try{return localStorage.getItem('hyoja-family')}catch(e){return 'ERR'}})()")
    try:
        tap(pg, '#hjFamily button:has-text("가족 저장하기")')
        pg.fill('#hjFamily input[aria-label*="이름"]', NAME)
        pg.fill('#hjFamily input[aria-label*="전화"]', PHONE_IN)
        pg.set_input_files('#hjFamily input[type=file]', {'name': 'p.jpg', 'mimeType': 'image/jpeg', 'buffer': jpeg_bytes()})
        pg.wait_for_timeout(700)
        tap(pg, '#hjFamily button:has-text("저장하기")'); pg.wait_for_timeout(500)
        st = fam_state()
        ok = bool(st) and PHONE_D in st and NAME in st
        rec(g, '이름·번호 저장', 'PASS' if ok else 'FAIL', (st or '')[:60].replace(NAME, '○') , None if ok else shot(pg, 'D_save_fail'))
        rec(g, '사진 저장(작게 줄인 JPEG)', 'PASS' if st and 'data:image/jpeg;base64,' in st and len(st) < 70000 else 'FAIL', f'저장 크기 {len(st or "")}바이트')
        href = pg.evaluate("(()=>{const a=document.querySelector('#hjFamily a[href^=\"tel:\"]');return a?a.getAttribute('href'):null})()")
        rec(g, '저장한 가족 전화 버튼(tel 링크, 누르면 전화 앱 화면까지만)', 'PASS' if href == 'tel:' + PHONE_D else 'FAIL', str(href))
        pg.reload(); pg.wait_for_timeout(1200)
        rec(g, '다시 열어도 유지(새로고침)', 'PASS' if fam_state() and PHONE_D in fam_state() and pg.locator('#hjFamily a[href^="tel:"]').count() == 1 else 'FAIL', '', shot(pg, 'D_after_reload'))
        ctx2 = b.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True)  # 다른 기기처럼 비어 있는지
        pg2 = ctx2.new_page(); pg2.goto(U + 'index.html'); pg2.wait_for_timeout(900)
        empty = pg2.evaluate("localStorage.getItem('hyoja-family')") is None
        rec(g, '저장값은 이 브라우저에만(다른 브라우저에는 없음)', 'PASS' if empty else 'FAIL'); ctx2.close()
        # 잘못된 입력
        tap(pg, '#hjFamily button:has-text("가족 저장하기")')
        msgs = {}
        for label, nm, ph in (('짧은 번호 거부', '둘째', '123'), ('같은 번호 중복 거부', '셋째', PHONE_IN)):
            pg.fill('#hjFamily input[aria-label*="이름"]', nm); pg.fill('#hjFamily input[aria-label*="전화"]', ph)
            tap(pg, '#hjFamily button:has-text("저장하기")'); pg.wait_for_timeout(250)
            m = pg.evaluate("(document.querySelector('#hjFamily [role=status]')||{}).innerText||''")
            before = json.loads(fam_state()); rec(g, label, 'PASS' if m and len(before) == 1 else 'FAIL', f'안내="{m}" 저장={len(before)}명')
        for i, ph in enumerate(('010-2222-3333', '010-4444-5555')):
            pg.fill('#hjFamily input[aria-label*="이름"]', f'가족{i}'); pg.fill('#hjFamily input[aria-label*="전화"]', ph)
            tap(pg, '#hjFamily button:has-text("저장하기")'); pg.wait_for_timeout(300)
            if i == 0: tap(pg, '#hjFamily button:has-text("가족 저장하기")')
        n = len(json.loads(fam_state()))
        has_add = pg.locator('#hjFamily button:has-text("가족 저장하기")').count()
        rec(g, '최대 3명(4번째 저장 버튼 없음)', 'PASS' if n == 3 and has_add == 0 else 'FAIL', f'{n}명, 저장 버튼 {has_add}개', shot(pg, 'D_three'))
        # 개인정보 외부 전송
        leak = [u for u, d in reqs if NAME in u or PHONE_D in u or PHONE_D in d or NAME in d or '%ED%81%B0%EB%94%B8' in u or 'base64' in u or 'base64' in d]
        rec(g, '이름·번호·사진이 외부로 전송되지 않음', 'PASS' if not leak else 'FAIL', f'전송 시도 {len(reqs)}건 중 개인정보 포함 {len(leak)}건 ' + str(leak)[:100])
        rec(g, '쿠키 0개', 'PASS' if pg.evaluate('document.cookie') == '' else 'FAIL')
        tap(pg, '#hjFamily button:has-text("저장한 가족 지우기")'); pg.wait_for_timeout(300)
        rec(g, '지우기 → 저장값 삭제', 'PASS' if json.loads(fam_state() or '[]') == [] else 'FAIL', fam_state() or '')
    except Exception as e:
        rec(g, '가족 전화 흐름', 'FAIL', str(e)[:200], shot(pg, 'D_flow_err'))
    rec(g, '실제 사진 선택(갤러리/카메라)·실제 전화 앱 화면', 'DEVICE', '사진 고르기 창과 전화 앱 화면은 갤럭시에서 확인(통화는 걸지 않기)')
    rec(g, '정책: 가족 전화는 사용자가 직접 입력한 번호(공식 번호 목록과 별개)', 'WARN', '초기 상태에는 가족 전화 링크가 0개. 사용자 입력 번호는 허용 목록 검사 대상이 아님. 대표 확인 필요')
    ctx.close()

    # ── E. 지역 저장 ──
    g = 'E 지역 저장'
    ctx, pg, reqs, errs = new_ctx(b)
    try:
        pg.goto(U + 'Regions.html'); pg.wait_for_selector('#region-mine-select'); pg.wait_for_timeout(500)
        opts = pg.evaluate("[...document.querySelectorAll('#region-mine-select option')].map(o=>[o.value,o.textContent])")
        pick = next((o for o in opts if '기흥' in o[1]), opts[1] if len(opts) > 1 else None)
        pg.select_option('#region-mine-select', pick[0]); pg.wait_for_timeout(400)
        pg.reload(); pg.wait_for_selector('#region-mine-name'); pg.wait_for_timeout(500)
        nm = pg.inner_text('#region-mine-name')
        rec(g, '지역 선택 후 새로고침해도 저장 표시', 'PASS' if '저장된 지역' in nm and pick[1] in nm else 'FAIL', nm, shot(pg, 'E_region'))
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1200)
        txt = pg.evaluate('document.body.innerText')
        rec(g, '첫 화면에도 저장한 지역이 보임', 'PASS' if pick[1] in txt else 'FAIL', f'기대={pick[1]}', None if pick[1] in txt else shot(pg, 'E_home_region'))
        leak = [u for u, d in reqs if pick[0] in u or pick[1] in u]
        rec(g, '지역 선택이 외부로 전송되지 않음', 'PASS' if not leak else 'FAIL', str(leak)[:100])
    except Exception as e:
        rec(g, '지역 저장 흐름', 'FAIL', str(e)[:200], shot(pg, 'E_err'))
    # 앱 재실행(브라우저 닫고 같은 저장소로 다시 열기)은 모의 환경에서 새로고침으로 대체
    rec(g, '앱을 완전히 닫았다 다시 켠 뒤 유지', 'DEVICE', '모의 검수는 새로고침으로 대체. 갤럭시에서 Chrome 완전 종료 후 확인')
    ctx.close()

    # ── F. 소리 읽기 ──
    g = 'F 소리 읽기'
    ctx, pg, reqs, errs = new_ctx(b)
    pg.goto(U + 'index.html'); pg.wait_for_timeout(1500); pg.evaluate(NOPREVENT)
    try:
        pg.evaluate("document.querySelector('.home-sound-settings').open=true"); pg.wait_for_timeout(200)
        tap(pg, '#hj-readbar button'); pg.wait_for_timeout(600)
        sp = pg.evaluate('window.__sp'); lab = pg.inner_text('#hj-readbar button')
        rec(g, '"소리로 읽어 주기" 누르면 읽기 시작', 'PASS' if sp['speak'] and lab == '멈추기' else 'FAIL', f'읽기 {len(sp["speak"])}건 버튼="{lab}"')
        tap(pg, '#hj-readbar button'); pg.wait_for_timeout(300)
        sp2 = pg.evaluate('window.__sp'); lab2 = pg.inner_text('#hj-readbar button')
        rec(g, '"멈추기" 누르면 멈춤', 'PASS' if sp2['cancel'] > sp['cancel'] and lab2 == '소리로 읽어 주기' else 'FAIL', f'취소 {sp2["cancel"]}회 버튼="{lab2}"')
        n0 = len(pg.evaluate('window.__sp.speak'))
        tap(pg, '.hj-say2'); pg.wait_for_timeout(500)
        sp3 = pg.evaluate('window.__sp'); url = pg.url
        rec(g, '급할 때 🔊: 그 버튼 내용만 읽고 화면 이동 없음', 'PASS' if len(sp3['speak']) > n0 and '급할' in sp3['speak'][-1] and url.endswith('index.html') else 'FAIL', f'읽은 말="{sp3["speak"][-1][:30] if sp3["speak"] else ""}" url={url.replace(U, "")}')
        pg.click('.hj-say2'); pg.wait_for_timeout(300)
        rec(g, '🔊를 다시 누르면 멈춤', 'PASS' if pg.evaluate('window.__sp.cancel') > sp2['cancel'] else 'FAIL')
        pg.goto(U + 'Emergency.html'); pg.wait_for_timeout(1200); pg.evaluate(NOPREVENT)
        n_say = pg.locator('.hj-say2').count()
        before = pg.url
        t = pg.locator('.hj-say2').first; t.evaluate("e=>e.scrollIntoView({block:'center'})"); t.click(); pg.wait_for_timeout(400)
        rec(g, '응급 화면 🔊 버튼은 전화를 걸지 않음(화면 그대로)', 'PASS' if n_say > 0 and pg.url == before else 'FAIL', f'🔊 {n_say}개')
    except Exception as e:
        rec(g, '소리 읽기 흐름', 'FAIL', str(e)[:200], shot(pg, 'F_err'))
    rec(g, '실제 한국어 음성 품질·볼륨·카카오톡 내부 브라우저 동작', 'DEVICE', '모의 브라우저는 음성을 내지 못해요. 갤럭시에서 직접 듣고 확인')
    ctx.close()

    # ── G. 버튼 크기·가로 넘침(첫 화면, 폭 320·360·390·412 × 글자 3단계) ──
    g = 'G 첫 화면 폭·글자·버튼'
    for w in (320, 360, 390, 412):
        for size in ('normal', 'large', 'xl'):
            ctx, pg, reqs, errs = new_ctx(b, w, 800)
            pg.add_init_script(f"try{{localStorage.setItem('hj-size','{size}')}}catch(e){{}}")
            pg.goto(U + 'index.html'); pg.wait_for_timeout(1300)
            try:
                kmap = {'normal': 'normal', 'large': 'large', 'xl': 'xl'}
                pg.evaluate(f"(()=>{{const b=document.querySelector('#sizeBtns button[data-k=\"{kmap[size]}\"],#hj-sizebar button[data-k=\"{kmap[size]}\"]');if(b)b.click();}})()")
                pg.wait_for_timeout(500)
            except Exception:
                pass
            r = pg.evaluate("""()=>{const de=document.documentElement;const over=Math.max(de.scrollWidth,document.body.scrollWidth)-de.clientWidth;
              const small=[...document.querySelectorAll('button,select,input,a.hj-tile,a.hj-urgent,.home-nav a,.hj-say2,summary')].filter(e=>{const s=getComputedStyle(e);if(!e.offsetParent||s.visibility==='hidden'||e.type==='file')return false;const b=e.getBoundingClientRect();return b.width>0&&(b.height<44||b.width<44)}).map(e=>(e.textContent||e.getAttribute('aria-label')||e.tagName).trim().slice(0,14)+':'+Math.round(e.getBoundingClientRect().width)+'x'+Math.round(e.getBoundingClientRect().height));
              const clip=[...document.querySelectorAll('a.hj-tile,a.hj-urgent,.home-nav a,button')].filter(e=>e.offsetParent&&e.scrollWidth>e.clientWidth+2&&getComputedStyle(e).overflow!=='visible').length;
              return {over,small,clip,active:[...document.querySelectorAll('#sizeBtns button,#hj-sizebar button')].filter(b=>b.getAttribute('aria-pressed')==='true').map(b=>b.textContent.trim())}}""")
            probs = []
            if r['over'] > 1: probs.append(f'가로 넘침 {r["over"]}px')
            if r['small']: probs.append('44px 미만 ' + ','.join(r['small'][:4]))
            if r['clip']: probs.append(f'글자 잘림 {r["clip"]}곳')
            if errs: probs.append('스크립트 오류')
            rec(g, f'{w}px · {size} · 눌림 상태 {r["active"]}', 'FAIL' if probs else 'PASS', ' / '.join(probs), shot(pg, f'G_{w}_{size}') if probs else None)
            ctx.close()
    b.close()

st = {k: sum(1 for r in R if r['status'] == k) for k in ('PASS', 'FAIL', 'WARN', 'DEVICE')}
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST')
groups = []
for r in R:
    if r['group'] not in groups: groups.append(r['group'])
md = [f'# 효자 2차 디자인 전용 검수 보고서', f'- 실행: {now}', f'- 전체 {len(R)}항목 · 통과 {st["PASS"]} · 실패 {st["FAIL"]} · 경고 {st["WARN"]} · 실기기 확인 필요 {st["DEVICE"]}',
      '- 결론: ' + ('**실패 있음 — 통과 처리 불가**' if st['FAIL'] else '**자동 항목 실패 없음 (실기기 확인 필요 항목은 별도)**'), '',
      '| 묶음 | 통과 | 실패 | 경고 | 실기기 확인 필요 |', '|---|---|---|---|---|']
for gname in groups:
    c = {k: sum(1 for r in R if r['group'] == gname and r['status'] == k) for k in ('PASS', 'FAIL', 'WARN', 'DEVICE')}
    md.append(f'| {gname} | {c["PASS"]} | {c["FAIL"]} | {c["WARN"]} | {c["DEVICE"]} |')
for title, key in (('실패 목록', 'FAIL'), ('경고', 'WARN'), ('실기기 확인 필요', 'DEVICE')):
    rows = [r for r in R if r['status'] == key]
    if rows:
        md += ['', f'## {title}'] + [f'- {r["group"]} · {r["name"]} — {r["detail"]}' + (f' (캡처: {r["shot"]})' if r['shot'] else '') for r in rows]
open(OUT + '/report.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
json.dump(dict(time=now, totals=st, results=R), open(OUT + '/report.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(md[:12]))
sys.exit(1 if st['FAIL'] else 0)
