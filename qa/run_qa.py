#!/usr/bin/env python3
"""효자 용인 휴대폰 자동검수기 (Playwright, 무료).

실행:  python3 qa/run_qa.py [--out qa-report] [--root .] [--only 그룹이름]
결과:  qa-report/report.md, report.json, screenshots/*.png(실패한 항목만)
종료코드: 실패가 1건이라도 있으면 1 (통과 처리 없음). 경고(WARN)는 통과로 세되 보고서에 따로 적는다.
이 검수기는 파일을 고치거나 배포하지 않고, 외부 서버로 아무것도 보내지 않는다(글꼴 서버 요청은 차단).
"""
import argparse, json, os, re, sys, threading, http.server, socketserver, functools, datetime
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='.')
ap.add_argument('--out', default='qa-report')
ap.add_argument('--only', default='')
a = ap.parse_args()
ROOT = os.path.abspath(a.root)
OUT = os.path.abspath(a.out)
SHOTS = os.path.join(OUT, 'screenshots')
os.makedirs(SHOTS, exist_ok=True)
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'qa_config.json'), encoding='utf-8'))
PAGES, WIDTHS, SIZES, TOL = CFG['pages'], CFG['widths'], CFG['sizes'], CFG['overflow_tolerance_px']
ALLOW, BLOCK, EM_ALLOW = set(CFG['allow_static']), CFG['block'], set(CFG['emergency_search_allow'])
SIZE_KO = {'normal': '보통', 'large': '크게', 'xl': '아주 크게'}

R = []  # 결과 목록


def rec(group, name, status, detail='', shot=None):
    R.append({'group': group, 'name': name, 'status': status, 'detail': detail, 'shot': shot})
    mark = {'PASS': '통과', 'FAIL': '실패', 'WARN': '경고'}[status]
    if status != 'PASS':
        print(f'[{mark}] {group} · {name} · {detail}')


def shot(pg, key):
    safe = re.sub(r'[^0-9A-Za-z가-힣_.-]+', '_', key)[:90]
    p = os.path.join(SHOTS, safe + '.png')
    try:
        pg.screenshot(path=p, full_page=True)
        return 'screenshots/' + safe + '.png'
    except Exception:
        return None


def digits_tokens(text):
    return {re.sub(r'\D', '', t) for t in re.findall(r'\d[\d\-\s]{5,}\d', text)}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *x):
        pass


handler = functools.partial(Quiet, directory=ROOT)
httpd = socketserver.TCPServer(('127.0.0.1', 0), handler)
PORT = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
U = f'http://127.0.0.1:{PORT}/'


def want(g):
    return (not a.only) or a.only == g


def new_page(b, w, size='normal', h=800):
    ctx = b.new_context(viewport={'width': w, 'height': h}, has_touch=True, is_mobile=True, device_scale_factor=2)
    pg = ctx.new_page()
    pg.route(re.compile(r'.*(fonts\.googleapis|fonts\.gstatic).*'), lambda r: r.abort())
    pg.goto(U + 'index.html')
    pg.evaluate("k=>{try{localStorage.setItem('hyoja-size',k)}catch(e){}}", size)
    return ctx, pg


with sync_playwright() as p:
    b = p.chromium.launch()

    # ── 1. 14개 화면 열림 ──
    if want('화면'):
        ctx, pg = new_page(b, 390)
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
        bad_req = []
        pg.on('response', lambda r: bad_req.append(r.url) if r.status >= 400 and r.url.startswith(U) else None)
        for name in PAGES:
            errs.clear(); bad_req.clear()
            pg.goto(U + name + '.html'); pg.wait_for_timeout(300)
            info = pg.evaluate("({t:document.title,n:document.body.innerText.trim().length})")
            ok = info['t'] and info['n'] > 50 and not errs and not bad_req
            rec('화면', f'{name}.html 열림', 'PASS' if ok else 'FAIL',
                '' if ok else f"제목={info['t']!r} 글자수={info['n']} 스크립트오류={errs[:2]} 없는파일={bad_req[:2]}",
                None if ok else shot(pg, f'open_{name}'))
        ctx.close()

    # ── 2. 화면 폭 × 글자 크기 ──
    if want('폭·글자'):
        for w in WIDTHS:
            for size in SIZES:
                ctx, pg = new_page(b, w, size)
                for name in PAGES:
                    pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
                    r = pg.evaluate("""()=>{const W=document.documentElement.clientWidth;let clip=0;
                      document.querySelectorAll('a[href^="tel:"],[data-hj-blocked]').forEach(a=>{const b=a.getBoundingClientRect();
                        const sp=[...a.querySelectorAll('span')].some(s=>s.getBoundingClientRect().right>b.right+1);
                        if(b.right>W+1||b.left<-1||sp)clip++});
                      return {sw:document.documentElement.scrollWidth,W,clip}}""")
                    key = f'{w}px · {SIZE_KO[size]} · {name}'
                    ov = r['sw'] - r['W']
                    if r['clip']:
                        rec('폭·글자', key, 'FAIL', f"번호 칸 잘림 {r['clip']}곳", shot(pg, f'clip_{w}_{size}_{name}'))
                    elif ov > TOL:
                        rec('폭·글자', key, 'FAIL', f"가로 넘침 {ov}px (너비 {r['sw']}/{r['W']})", shot(pg, f'over_{w}_{size}_{name}'))
                    elif ov > 0:
                        rec('폭·글자', key, 'WARN', f'가로 {ov}px 어긋남(허용 {TOL}px 이내) — 실기기 확인 권장', shot(pg, f'warn_{w}_{size}_{name}'))
                    else:
                        rec('폭·글자', key, 'PASS')
                ctx.close()

    # ── 3. 전화 버튼·미확인 번호 ──
    if want('전화'):
        ctx, pg = new_page(b, 390)
        for name in PAGES:
            pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
            tels = pg.evaluate("[...document.querySelectorAll('a[href^=\"tel:\"]')].map(a=>a.getAttribute('href').slice(4).replace(/\\D/g,''))")
            shown = digits_tokens(pg.evaluate('document.body.innerText'))
            out = sorted({t for t in tels if t not in ALLOW})
            hid = sorted({t for t in set(tels) | shown if t in BLOCK})
            if out or hid:
                rec('전화', f'{name}.html 전화 링크', 'FAIL',
                    f'공식 확인 목록 밖 {out} / 숨겨야 할 번호 노출 {hid}', shot(pg, f'tel_{name}'))
            else:
                rec('전화', f'{name}.html 전화 링크 {len(tels)}개', 'PASS')
        pg.goto(U + 'Centers.html'); pg.wait_for_timeout(250)
        c = pg.evaluate("({tel:document.querySelectorAll('a[href^=\"tel:\"]').length,blk:[...document.querySelectorAll('[data-hj-blocked]')].map(e=>e.innerText)})")
        ok = c['tel'] == CFG['centers']['tel_count'] and len(c['blk']) == CFG['centers']['blocked_count'] and all(CFG['centers']['blocked_text'] in t for t in c['blk'])
        rec('전화', f"주민센터 전화 {c['tel']}개 + 공식 확인 중 {len(c['blk'])}개", 'PASS' if ok else 'FAIL',
            '' if ok else f"기대값 {CFG['centers']}", None if ok else shot(pg, 'centers_counts'))
        # 주민센터는 검색창이 없는 목록형이므로 동 이름 목록으로 대신 점검
        names = pg.evaluate("[...document.querySelectorAll('a[href^=\"tel:\"],[data-hj-blocked]')].length")
        rec('전화', '주민센터 목록 전체(전화+확인중) 39개', 'PASS' if names == 39 else 'FAIL', '' if names == 39 else f'{names}개')
        ctx.close()

    # ── 4. 병원·약국 검색 ──
    if want('전화'):
        # 자료 파일(data/*.json) 안의 자유 입력 글에 전화번호 모양이 남아 있으면 안 된다(화면에 안 보여도 공개 파일이므로).
        PH = re.compile(r'(?<!\d)(?:\+?82[-\s.]?)?0\d{1,2}[-\s.)]?\d{3,4}[-\s.]?\d{4}(?!\d)|(?<!\d)1[5-9]\d{2}[-\s]?\d{4}(?!\d)')
        for fn in ('pharmacy', 'emergency'):
            try:
                rows = json.load(open(os.path.join(ROOT, 'data', fn + '.json'), encoding='utf-8'))['목록']
            except Exception as e:
                rec('전화', f'자료 파일 {fn}.json 자유 입력 글 번호 검사', 'FAIL', f'읽기 실패: {e}'); continue
            hit = sum(1 for p in rows for k in ('dutyEtc', 'dutyInf', 'dutyMapimg') if PH.search(str(p.get(k) or '')))
            rec('전화', f'자료 파일 {fn}.json 자유 입력 글 전화번호 {hit}건 (0건이어야 함)', 'FAIL' if hit else 'PASS', f'{hit}건 남아 있음' if hit else '')

    if want('검색'):
        ctx, pg = new_page(b, 390)
        pg.goto(U + 'Emergency.html'); pg.wait_for_selector('#medicalKind')

        def search(kind, gu, q=''):
            pg.select_option('#medicalKind', kind); pg.select_option('#medicalGu', gu)
            pg.fill('#medicalQuery', q); pg.click('#medicalSearchForm button[type=submit]'); pg.wait_for_timeout(600)
            for _ in range(80):
                m = pg.locator('#medicalSearchMore')
                if m.is_visible():
                    m.click(); pg.wait_for_timeout(40)
                else:
                    break
            return pg.evaluate("""()=>{const c=[...document.querySelectorAll('#medicalSearchResults article')];
              return {cards:c.length,tel:[...document.querySelectorAll('#medicalSearchResults a[href^=tel]')].map(a=>a.getAttribute('href').slice(4)),
              maps:document.querySelectorAll('#medicalSearchResults a[href*="map"],#medicalSearchResults a[href*="kakao"],#medicalSearchResults a[href*="naver"],#medicalSearchResults a[href*="google"]').length,
              status:(document.getElementById('medicalSearchStatus')||{}).innerText||'',text:(document.getElementById('medicalSearchResults')||{}).innerText||''}}""")
        cases = [('pharmacy', g, '') for g in ('', '처인구', '기흥구', '수지구')] + [('pharmacy', '', '동백중앙로'), ('pharmacy', '', '약국'),
                 ('emergency', '', ''), ('emergency', '처인구', ''), ('emergency', '기흥구', ''), ('emergency', '수지구', '')]
        for kind, gu, q in cases:
            r = search(kind, gu, q)
            label = f"{'약국' if kind == 'pharmacy' else '응급의료기관'} · {gu or '전체'}{' · ' + q if q else ''}"
            probs = []
            if kind == 'pharmacy':
                if r['tel']: probs.append(f"약국 전화 버튼 {len(r['tel'])}개 노출")
                if r['cards'] == 0: probs.append('결과 0건')
                if re.search(r'전화(로|해서)? ?(확인|문의|물어)', r['text'] + r['status']): probs.append('약국 결과에 "전화로 확인" 문구(전화 버튼은 숨김 정책과 모순)')
            else:
                bad = [t for t in r['tel'] if t not in EM_ALLOW]
                if bad: probs.append(f'승인 목록 밖 번호 {bad}')
                if r['cards'] == 0 and '찾지 못했어요' not in r['status']: probs.append('결과 0건인데 안내 문구 없음')
            if r['cards'] and r['maps'] == 0: probs.append('지도 버튼 없음')
            rec('검색', label + f" ({r['cards']}건)", 'FAIL' if probs else 'PASS', ' / '.join(probs), shot(pg, 'search_' + label) if probs else None)
        # 응급 화면 '지금 문 연 약국' 목록
        pg.goto(U + 'Emergency.html'); pg.wait_for_selector('button.gu')
        for gu in ('처인구', '기흥구', '수지구'):
            pg.click(f'button.gu[data-gu={gu}]'); pg.wait_for_timeout(500)
            r = pg.evaluate("({items:document.querySelectorAll('#phList > *').length,all:((document.getElementById('phStatus')||{}).innerText||'')+((document.getElementById('phSrc')||{}).innerText||'')+((document.getElementById('phList')||{}).innerText||''),tel:document.querySelectorAll('#phList a[href^=tel]').length,msg:(document.getElementById('phStatus')||{}).innerText||''})")
            probs = []
            if r['tel']: probs.append(f"전화 버튼 {r['tel']}개 노출")
            if re.search(r'전화(로|해서)? ?(확인|문의|물어)', r['all']): probs.append('문 연 약국 영역에 "전화로 확인" 문구')
            # 시간표상 지금 문 연 약국이 없는 시간대에는 0건이 정상이다. 이때는 안내 문구가 있어야 한다.
            if r['items'] == 0 and '찾지 못했어요' not in r['msg']: probs.append('목록 0건인데 안내 문구 없음')
            rec('검색', f'지금 문 연 약국 · {gu} ({r["items"]}건)', 'FAIL' if probs else 'PASS', ' / '.join(probs), shot(pg, 'phlist_' + gu) if probs else None)
        ctx.close()

    # ── 5. 오프라인 캐시·재접속 ──
    if want('오프라인'):
        ctx, pg = new_page(b, 390)
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1500)
        for name in PAGES:
            pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1500)
        sw = pg.evaluate("navigator.serviceWorker.controller?navigator.serviceWorker.controller.scriptURL.split('/').pop():null")
        caches_ = pg.evaluate("caches.keys()")
        rec('오프라인', '서비스워커 작동·저장소 생성', 'PASS' if sw == 'sw.js' and caches_ else 'FAIL', f'sw={sw} 저장소={caches_}',
            None if sw == 'sw.js' and caches_ else shot(pg, 'offline_sw'))
        ctx.set_offline(True)
        for name in PAGES:
            try:
                pg.goto(U + name + '.html', timeout=15000); pg.wait_for_timeout(300)
                n = pg.evaluate('document.body.innerText.trim().length')
                rec('오프라인', f'{name}.html 비행기 모드에서 열림', 'PASS' if n > 50 else 'FAIL', '' if n > 50 else f'글자수 {n}', None if n > 50 else shot(pg, f'offline_{name}'))
            except Exception as e:
                rec('오프라인', f'{name}.html 비행기 모드에서 열림', 'FAIL', str(e)[:100])
        ctx.set_offline(False)
        pg.goto(U + 'Centers.html'); pg.wait_for_timeout(500)
        n = pg.evaluate("document.querySelectorAll('a[href^=\"tel:\"]').length")
        rec('오프라인', '재접속 후 주민센터 전화 37개 복원', 'PASS' if n == 37 else 'FAIL', '' if n == 37 else f'{n}개')
        ctx.close()

    # ── 6. 익명 통계 (외부 전송 없이 모의 시험) ──
    if want('통계'):
        import mimetypes
        ALLOWED = re.compile(r'^(search-(pharmacy|emergency)-(all|chein|giheung|suji)-q[01]|tel-[a-z]{2,12}|map-(pharmacy|emergency)|gu-(chein|giheung|suji)|size-(normal|large|xl))$')
        PATHRE = re.compile(r'^/[A-Za-z0-9_.\-]*$')
        QUERY = '동백중앙로'
        STOP = ('goatcounter.com', 'zgo.at')
        NOPREVENT = """document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');if(a&&/^(tel:|https:\\/\\/map\\.)/.test(a.getAttribute('href')||''))e.preventDefault();});"""

        def stats_ctx(init=None, w=390):
            ctx = b.new_context(viewport={'width': w, 'height': 800}, has_touch=True, is_mobile=True)
            pg = ctx.new_page()
            pg.route(re.compile(r'.*(fonts\.googleapis|fonts\.gstatic).*'), lambda r: r.abort())
            pg.route(re.compile(r'https://map\.(naver|kakao)\.com/.*'), lambda r: r.abort())
            if init:
                ctx.add_init_script(init)
            reqs = []
            ctx.on('request', lambda r: reqs.append((r.url, r.headers)) if not r.url.startswith(U) and not r.url.startswith('data:') else None)
            errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)[:100]))
            return ctx, pg, reqs, errs

        def drive(pg):
            """대표적인 이용 흐름: 홈 → 응급 → 약국 검색(검색어 입력) → 지도 → 문 연 약국 구 선택 → 글자 크기 → 주민센터 전화 클릭"""
            pg.goto(U + 'index.html'); pg.wait_for_timeout(400)
            pg.goto(U + 'Emergency.html'); pg.wait_for_selector('#medicalKind'); pg.wait_for_timeout(300)
            pg.evaluate(NOPREVENT)
            pg.select_option('#medicalKind', 'pharmacy'); pg.select_option('#medicalGu', '기흥구'); pg.fill('#medicalQuery', QUERY)
            pg.click('#medicalSearchForm button[type=submit]'); pg.wait_for_timeout(700)
            m = pg.locator('#medicalSearchResults a[href*="map."]').first
            if m.count(): m.click(); pg.wait_for_timeout(200)
            pg.select_option('#medicalKind', 'emergency'); pg.select_option('#medicalGu', ''); pg.fill('#medicalQuery', '')
            pg.click('#medicalSearchForm button[type=submit]'); pg.wait_for_timeout(500)
            t = pg.locator('#medicalSearchResults a[href^="tel:"]').first
            if t.count(): t.click(); pg.wait_for_timeout(150)
            pg.click('button.gu[data-gu=수지구]'); pg.wait_for_timeout(300)
            pg.click('#hj-sizebar button[data-k=large]'); pg.wait_for_timeout(200)
            pg.goto(U + 'Centers.html'); pg.wait_for_timeout(300); pg.evaluate(NOPREVENT)
            pg.locator('a[href^="tel:"]').first.click(); pg.wait_for_timeout(150)

        # (가) 기본 상태: 통계 코드가 비어 있어 아무것도 보내지 않는다
        ctx, pg, reqs, errs = stats_ctx()
        drive(pg)
        hosts = sorted({re.sub(r'^https?://([^/]+)/.*', r'\1', u) for u, _ in reqs})
        bad = [h for h in hosts if any(x in h for x in STOP)]
        KNOWN = ('api.open-meteo.com', 'air-quality-api.open-meteo.com')      # 날씨·대기질(고정 좌표)
        FONTS = ('fonts.googleapis.com', 'fonts.gstatic.com')                 # 구글 글꼴(자체 보관으로 바꾼 뒤에는 접속하면 안 됨)
        extra = [h for h in hosts if h not in KNOWN and not any(x in h for x in STOP)]
        rec('통계', '(가) 기본 상태: 날씨 외 외부 요청 0건(구글 글꼴 포함)', 'FAIL' if extra else 'PASS', f'예상 밖 외부 주소 {extra}' if extra else '', shot(pg, 'stats_hosts') if extra else None)
        ctx.close()

        # (나) 모의 기록 모드: 통계가 만드는 이벤트 이름만 기록(전송 없음)
        ctx, pg, reqs, errs = stats_ctx("window.__HJ_STATS_TEST={sink:(window.__hjLog=JSON.parse(sessionStorage.getItem('__t')||'[]')),allowLocal:true};window.addEventListener('pagehide',()=>{try{sessionStorage.setItem('__t',JSON.stringify(window.__hjLog))}catch(e){}});")
        drive(pg)
        pg.evaluate("sessionStorage.setItem('__t',JSON.stringify(window.__hjLog))")
        collected = pg.evaluate('window.__hjLog')
        cookies = ctx.cookies()
        ls = pg.evaluate("Object.keys(localStorage)")
        names = [x['name'] for x in collected]
        badn = [n for n in names if not (ALLOWED.match(n) or PATHRE.match(n))]
        rec('통계', f'(나) 기록된 이벤트 {len(names)}건 모두 허용 형식', 'FAIL' if badn else 'PASS', f'허용 밖 이름 {badn}' if badn else '', shot(pg, 'stats_names') if badn else None)
        need = ['search-pharmacy-giheung-q1', 'search-emergency-all-q0', 'gu-suji', 'size-large', 'tel-centers']
        miss = [n for n in need if n not in names]
        rec('통계', '(나) 핵심 이용 이벤트 기록(검색·구 선택·글자 크기·전화 클릭)', 'FAIL' if miss else 'PASS', f'기록 안 됨 {miss}' if miss else '', shot(pg, 'stats_missing') if miss else None)
        rec('통계', '(나) 방문 기록(주소 경로만)', 'PASS' if any(PATHRE.match(n) for n in names) else 'FAIL', '' if any(PATHRE.match(n) for n in names) else '방문 기록 없음')
        blob = json.dumps(collected, ensure_ascii=False)
        leaks = []
        if QUERY in blob: leaks.append('검색어 원문')
        if re.search(r'\d{5,}', blob): leaks.append('긴 숫자(전화번호 가능성)')
        if re.search(r'0\d{1,2}-?\d{3,4}-?\d{4}', blob): leaks.append('전화번호 형식')
        if re.search(r'병원|약국|의원|센터', blob): leaks.append('기관 이름')
        rec('통계', '(나) 기록에 검색어·전화번호·기관 이름 없음', 'FAIL' if leaks else 'PASS', ' / '.join(leaks), shot(pg, 'stats_leak') if leaks else None)
        rec('통계', '(나) 쿠키 0개', 'PASS' if not cookies else 'FAIL', '' if not cookies else f'쿠키 {len(cookies)}개')
        ls_bad = [k for k in ls if k not in ('hyoja-size', 'hj-sound', 'hyoja-sound', 'hyoja-vol')]
        rec('통계', '(나) 통계용 저장소(localStorage) 사용 없음', 'PASS' if not ls_bad else 'WARN', f'확인할 저장 키 {ls_bad}' if ls_bad else '')
        ctx.close()

        # (다) 전송 경로 점검: 가짜 사이트 코드로 켜고, 통계 서버 요청은 밖으로 나가기 전에 막아 내용만 검사
        ctx, pg, reqs, errs = stats_ctx("window.__HJ_STATS_TEST={code:'hyoja-qa-test',sink:[],allowLocal:true};")
        seen = []
        def grab(route):
            seen.append((route.request.url, route.request.headers)); route.abort()
        ctx.route(re.compile(r'https://[a-z0-9-]+\.goatcounter\.com/.*'), grab)
        drive(pg)
        problems = []
        from urllib.parse import urlparse, parse_qs, unquote
        for url, hd in seen:
            u_ = urlparse(url); q_ = parse_qs(u_.query)
            if u_.hostname != 'hyoja-qa-test.goatcounter.com': problems.append(f'다른 서버 {u_.hostname}')
            if u_.path != '/count': problems.append(f'경로 {u_.path}')
            extra_keys = set(q_) - {'p', 't', 'e', 's', 'rnd'}
            if extra_keys: problems.append(f'예상 밖 항목 {sorted(extra_keys)}')
            pv = unquote(q_.get('p', [''])[0])
            if not (ALLOWED.match(pv) or PATHRE.match(pv)): problems.append(f'p 값 {pv!r}')
            if QUERY in url or re.search(r'%EB%8F%99%EB%B0%B1', url): problems.append('검색어 포함')
            if 'referer' in {k.lower() for k in hd}: problems.append('Referer 헤더 전송')
            if 'cookie' in {k.lower() for k in hd}: problems.append('Cookie 헤더 전송')
        rec('통계', f'(다) 전송 요청 {len(seen)}건: 주소·항목·내용 검사', 'FAIL' if problems or not seen else 'PASS',
            ' / '.join(sorted(set(problems))) if problems else ('요청이 하나도 만들어지지 않음' if not seen else ''), shot(pg, 'stats_send') if problems or not seen else None)
        rec('통계', '(다) 통계 서버가 막혀도 앱 오류 0건', 'FAIL' if errs else 'PASS', f'{errs[:2]}' if errs else '', shot(pg, 'stats_err') if errs else None)
        third = [u for u, _ in reqs if any(x in u for x in ('zgo.at',))]
        rec('통계', '(다) 외부 통계 스크립트(gc.zgo.at) 불러오지 않음', 'FAIL' if third else 'PASS', f'{third[:1]}' if third else '')
        ctx.close()

        # (라) 추적 거부(Do Not Track) 신호가 있으면 아무것도 기록하지 않는다
        ctx, pg, reqs, errs = stats_ctx("Object.defineProperty(navigator,'doNotTrack',{get:()=>'1'});window.__HJ_STATS_TEST={code:'hyoja-qa-test',sink:(window.__hjLog=[]),allowLocal:true};")
        pg.goto(U + 'Emergency.html'); pg.wait_for_selector('#medicalKind'); pg.wait_for_timeout(300)
        pg.select_option('#medicalKind', 'pharmacy'); pg.click('#medicalSearchForm button[type=submit]'); pg.wait_for_timeout(400)
        n = pg.evaluate('window.__hjLog.length'); gc = [u for u, _ in reqs if 'goatcounter' in u]
        rec('통계', '(라) 추적 거부 신호 시 기록 0건·전송 0건', 'PASS' if n == 0 and not gc else 'FAIL', '' if n == 0 and not gc else f'기록 {n}건 전송 {len(gc)}건')
        ctx.close()

        # (마) 실제 사이트 주소처럼 보이는 곳에서는 시험용 설정을 무시한다
        ctx = b.new_context(viewport={'width': 390, 'height': 800}); pg = ctx.new_page()
        ctx.add_init_script("window.__HJ_STATS_TEST={code:'hyoja-qa-test',sink:(window.__hjLog=[]),allowLocal:true};")
        gcreq = []
        def fake(route):
            r = route.request; u_ = urlparse(r.url)
            if 'goatcounter' in (u_.hostname or ''): gcreq.append(r.url); return route.abort()
            if u_.hostname == 'hyoja-qa.example':
                f = os.path.join(ROOT, u_.path.lstrip('/') or 'index.html')
                if os.path.isfile(f):
                    return route.fulfill(status=200, body=open(f, 'rb').read(), content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
                return route.fulfill(status=404, body='')
            return route.abort()
        ctx.route('**/*', fake)
        pg.goto('https://hyoja-qa.example/index.html'); pg.wait_for_timeout(800)
        n = pg.evaluate('(window.__hjLog||[]).length')
        rec('통계', '(마) 실제 주소에서는 시험용 설정 무시(기록 0·전송 0)', 'PASS' if n == 0 and not gcreq else 'FAIL', '' if n == 0 and not gcreq else f'기록 {n}건 전송 {len(gcreq)}건')
        ctx.close()


    # ── 7. 글꼴 자체 보관 ──
    if want('글꼴'):
        FONT_HOSTS = ('fonts.googleapis.com', 'fonts.gstatic.com')
        ctx = b.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
        pg = ctx.new_page(); hosts_seen = []; font_reqs = []
        ctx.on('request', lambda r: hosts_seen.append(r.url) if any(h in r.url for h in FONT_HOSTS) else None)
        ctx.on('response', lambda r: font_reqs.append((r.url.split('/')[-1], r.status)) if '/fonts/' in r.url else None)
        bad = []
        for name in PAGES:
            pg.goto(U + name + '.html'); pg.wait_for_timeout(250)
        rec('글꼴', '14개 화면에서 구글 글꼴 서버 접속 0건', 'FAIL' if hosts_seen else 'PASS', f'{hosts_seen[:2]}' if hosts_seen else '')
        pg.goto(U + 'Emergency.html'); pg.wait_for_timeout(300)
        ok = pg.evaluate("document.fonts.load('400 16px \"Noto Sans KR\"','가나다').then(f=>f.length)")
        ok9 = pg.evaluate("document.fonts.load('900 16px \"Noto Sans KR\"','응급').then(f=>f.length)")
        got = [n for n, st in font_reqs if st == 200]
        rec('글꼴', '자체 보관 글꼴(자주 쓰는 글자) 내려받기·적용', 'PASS' if ok and ok9 and 'noto-sans-kr-a.woff' in got else 'FAIL', f'faces={ok}/{ok9} 받은 파일={got}', None if ok and ok9 else shot(pg, 'font_a'))
        RARE = '뷁'
        r = pg.evaluate("(c)=>document.fonts.load('400 16px \"Noto Sans KR\"',c).then(f=>f.length)", RARE)
        got = [n for n, st in font_reqs if st == 200]
        rec('글꼴', f'드문 글자({RARE}) 구간 내려받기', 'PASS' if r and 'noto-sans-kr-b.woff' in got else 'FAIL', f'faces={r} 받은 파일={got}', None if r else shot(pg, 'font_b'))
        w = pg.evaluate("(()=>{const e=document.createElement('span');e.style.cssText='font:700 20px \"Noto Sans KR\";position:absolute;visibility:hidden';e.textContent='응급 병원 약국';document.body.appendChild(e);const a=e.getBoundingClientRect().width;e.style.fontFamily='serif';const b=e.getBoundingClientRect().width;return [a,b]})()")
        rec('글꼴', '글꼴이 실제 글자 폭에 적용됨(대체 글꼴과 다름)', 'PASS' if abs(w[0] - w[1]) > 0.5 else 'FAIL', f'폭 {w}')
        # 비행기 모드에서도 글꼴 사용
        pg.goto(U + 'index.html'); pg.wait_for_timeout(1500); pg.goto(U + 'index.html'); pg.wait_for_timeout(500)
        ctx.set_offline(True)
        try:
            pg.goto(U + 'Emergency.html', timeout=15000); pg.wait_for_timeout(400)
            off = pg.evaluate("document.fonts.load('400 16px \"Noto Sans KR\"','가').then(f=>f.length)")
            rec('글꼴', '비행기 모드에서도 자체 글꼴 적용', 'PASS' if off else 'FAIL', f'faces={off}', None if off else shot(pg, 'font_offline'))
        except Exception as e:
            rec('글꼴', '비행기 모드에서도 자체 글꼴 적용', 'FAIL', str(e)[:100])
        ctx.close()

    b.close()
httpd.shutdown()

# ── 보고서 ──
now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d %H:%M KST')
groups = {}
for r in R:
    groups.setdefault(r['group'], []).append(r)
tot = {s: sum(1 for r in R if r['status'] == s) for s in ('PASS', 'WARN', 'FAIL')}
L = [f'# 효자 용인 휴대폰 자동검수 보고서', f'- 실행: {now}', f'- 전체 {len(R)}항목 · 통과 {tot["PASS"]} · 경고 {tot["WARN"]} · 실패 {tot["FAIL"]}',
     f'- 결론: **{"실패 있음 — 통과 처리 불가" if tot["FAIL"] else "실패 없음 (경고는 아래 확인)"}**', '',
     '| 묶음 | 항목 | 통과 | 경고 | 실패 |', '|---|---|---|---|---|']
for g, rs in groups.items():
    L.append(f'| {g} | {len(rs)} | ' + ' | '.join(str(sum(1 for r in rs if r["status"] == s)) for s in ("PASS", "WARN", "FAIL")) + ' |')
for title, st in (('실패 목록', 'FAIL'), ('경고 목록', 'WARN')):
    xs = [r for r in R if r['status'] == st]
    if xs:
        L += ['', f'## {title}']
        for r in xs:
            L.append(f"- {r['group']} · {r['name']} — {r['detail']}" + (f" (캡처: {r['shot']})" if r['shot'] else ''))
open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
json.dump({'time': now, 'totals': tot, 'results': R}, open(os.path.join(OUT, 'report.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n'.join(L[:8]))
sys.exit(1 if tot['FAIL'] else 0)
