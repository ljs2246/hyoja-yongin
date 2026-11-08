#!/usr/bin/env python3
"""Google Drive 안전 업로더(생성 전용). 기존 파일 수정·삭제·덮어쓰기 없음.
인증: 환경변수 DRIVE_ACCESS_TOKEN (전용 서비스계정의 drive.file 범위 단기 토큰). 코드·저장소에 비밀정보를 두지 않는다.
안전장치: ①허용 폴더(09 신규공동작업의 00~08)만 ②파일명 규칙 [신규-상태]_YYYY-MM-DD_번호_담당자_내용_vNN ③같은 폴더 같은 이름 있으면 건너뜀 ④내용 해시가 같은 파일이 이미 있으면 건너뜀 ⑤기본은 시험(dry-run), --apply 가 있어야 실제 생성.
사용: drive-upload.py --folder 00 --file PATH [--name 이름] [--apply]"""
import os,sys,re,json,hashlib,urllib.request,urllib.parse,argparse,datetime,uuid
API=os.environ.get('DRIVE_API_BASE','https://www.googleapis.com')
FOLDERS={'00':'1QsJ7YZ0YnqfK8J6r7orcsBPOSOIDIPgH','01':'1ozLDMVkoMsaHlfFLPu0ffx50TqmnmTnQ','02':'1-VHlCkVN3-oik7FAUGoKr5F5B4bWMtzT','03':'1zV65R5HPx7dX4jgiLkktRJiElyF97dEX','04':'1PUmYONKlnwtDq7UEYtSsrB3mEeHQ2aqy','05':'1qtvs4zyESNZX_FgGE6xxjva_zz6Lg0qe','06':'1Suz1qNNKgMF-cREx_JBf7CbcAs0swSQn','07':'1MBrLghH11g4Zm39AIGWoyqmkLzD-edj5','08':'1EB6Tq4OKIeWokXtb9TLZQFjq9YKmHN6u'}
NAME=re.compile(r'^\[신규-(작업중|검수중|승인완료|보류)\]_\d{4}-\d{2}-\d{2}_\d{3}_[^_]+_.+_v\d{2}(\.[A-Za-z0-9]+)?$')
def call(method,url,data=None,headers=None):
    h={'Authorization':'Bearer '+os.environ['DRIVE_ACCESS_TOKEN']};h.update(headers or {})
    r=urllib.request.Request(url,data=data,method=method,headers=h)
    with urllib.request.urlopen(r,timeout=30) as f:return json.loads(f.read() or b'{}')
def find(parent,q_extra):
    q=f"'{parent}' in parents and trashed=false and {q_extra}"
    return call('GET',f"{API}/drive/v3/files?"+urllib.parse.urlencode({'q':q,'fields':'files(id,name,appProperties)','supportsAllDrives':'true'})).get('files',[])
def run(folder,path,name=None,apply=False):
    res={'task':'드라이브 자동 저장','department':'05 구글 드라이브 문서관리 담당','runId':datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6],'folder':folder,'file':os.path.basename(path),'approver':None}
    name=name or os.path.basename(path)
    if folder not in FOLDERS: res['result']='거부(허용 폴더 아님)';return res
    if not NAME.match(name): res['result']='거부(파일명 규칙 위반)';return res
    if not os.environ.get('DRIVE_ACCESS_TOKEN'): res['result']='중단(인증 없음)';return res
    body=open(path,'rb').read();h=hashlib.sha256(body).hexdigest();parent=FOLDERS[folder]
    if find(parent,"name='%s'"%name.replace("'","\\'")): res['result']='건너뜀(같은 이름 존재: 새 버전 번호로 저장하세요)';return res
    same=[f for f in find(parent,"appProperties has { key='sha256' and value='%s' }"%h)]
    if same: res['result']='건너뜀(같은 내용 파일 존재: %s)'%same[0]['name'];return res
    if not apply: res['result']='시험 통과(생성하지 않음, --apply 필요)';return res
    b='bnd'+uuid.uuid4().hex
    meta=json.dumps({'name':name,'parents':[parent],'appProperties':{'sha256':h,'source':'hyoja-automation'}}).encode()
    mp=(f'--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n').encode()+meta+(f'\r\n--{b}\r\nContent-Type: text/plain\r\n\r\n').encode()+body+f'\r\n--{b}--'.encode()
    out=call('POST',f"{API}/upload/drive/v3/files?uploadType=multipart&supportsAllDrives=true&fields=id,name",mp,{'Content-Type':'multipart/related; boundary='+b})
    res['result']='생성';res['driveId']=out.get('id');return res
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--folder',required=True);a.add_argument('--file',required=True);a.add_argument('--name');a.add_argument('--apply',action='store_true');a.add_argument('--log',default='docs/runs')
    x=a.parse_args()
    try:r=run(x.folder,x.file,x.name,x.apply)
    except Exception as e:r={'result':'실패(%s)'%type(e).__name__,'folder':x.folder}
    os.makedirs(x.log,exist_ok=True);json.dump(r,open(os.path.join(x.log,'drive-'+r.get('runId','x')+'.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(r['result']);sys.exit(0 if r['result'].startswith(('생성','시험 통과','건너뜀')) else 1)
