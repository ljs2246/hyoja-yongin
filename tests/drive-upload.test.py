#!/usr/bin/env python3
"""Drive 업로더 시험(가짜 Drive 서버 사용: 실제 드라이브·인증 사용 안 함)"""
import threading,http.server,json,os,sys,subprocess,tempfile,urllib.parse,re
STORE=[]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(s,*a):pass
    def do_GET(s):
        q=urllib.parse.parse_qs(urllib.parse.urlparse(s.path).query).get('q',[''])[0]
        out=[]
        for f in STORE:
            if f"name='{f['name']}'" in q or (f['sha'] and f"value='{f['sha']}'" in q): out.append({'id':f['id'],'name':f['name']})
        s.send_response(200);s.end_headers();s.wfile.write(json.dumps({'files':out}).encode())
    def do_POST(s):
        n=int(s.headers['Content-Length']);b=s.rfile.read(n).decode('utf-8','replace')
        meta=json.loads(b.split('\r\n\r\n')[1].split('\r\n')[0])
        STORE.append({'id':'F%d'%(len(STORE)+1),'name':meta['name'],'sha':meta['appProperties']['sha256'],'auth':s.headers.get('Authorization')})
        s.send_response(200);s.end_headers();s.wfile.write(json.dumps({'id':STORE[-1]['id'],'name':meta['name']}).encode())
srv=http.server.HTTPServer(('127.0.0.1',0),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
env=dict(os.environ,DRIVE_API_BASE=f'http://127.0.0.1:{srv.server_port}',DRIVE_ACCESS_TOKEN='TEST-TOKEN')
d=tempfile.mkdtemp();R=[]
def up(folder,name,content,apply=True,token=True):
    p=os.path.join(d,'x.md');open(p,'w').write(content)
    e=dict(env)
    if not token:e.pop('DRIVE_ACCESS_TOKEN')
    r=subprocess.run([sys.executable,'scripts/drive-upload.py','--folder',folder,'--file',p,'--name',name,'--log',d]+(['--apply'] if apply else []),capture_output=True,text=True,env=e)
    return r.stdout.strip(),r.returncode
def t(n,ok):R.append(ok);print('통과' if ok else '실패',n)
N='[신규-작업중]_2026-10-30_101_클로드_업로더시험_v01.md'
o,_=up('00',N,'hello',apply=False);t('시험 모드: 생성하지 않음',o.startswith('시험 통과') and not STORE)
o,_=up('00',N,'hello');t('정상 생성 1건·토큰 전달',o=='생성' and len(STORE)==1 and STORE[0]['auth']=='Bearer TEST-TOKEN')
o,rc=up('00',N,'다른 내용');t('같은 이름은 덮어쓰지 않고 건너뜀',o.startswith('건너뜀(같은 이름') and len(STORE)==1)
o,_=up('00','[신규-작업중]_2026-10-30_102_클로드_복사본_v01.md','hello');t('같은 내용은 이름이 달라도 중복 생성 안 함',o.startswith('건너뜀(같은 내용') and len(STORE)==1)
o,rc=up('00','검수중_2026-10-30_002_클로드_옛이름_v01.md','zzz');t('규칙 위반 파일명 거부',o.startswith('거부(파일명') and rc!=0 and len(STORE)==1)
o,rc=up('99',N,'q');t('허용되지 않은 폴더 거부',o.startswith('거부(허용') and len(STORE)==1)
o,rc=up('00','[신규-검수중]_2026-10-30_103_클로드_토큰없음_v01.md','q',token=False);t('인증 없으면 중단',o.startswith('중단') and len(STORE)==1)
o,_=up('02','[신규-검수중]_2026-10-30_104_클로드_새파일_v01.md','새 내용');t('새 이름·새 내용은 생성',o=='생성' and len(STORE)==2)
print(f'통과 {sum(R)} / 전체 {len(R)}');sys.exit(0 if all(R) else 1)
