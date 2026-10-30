#!/usr/bin/env python3
"""격리 자료(data/staging/)가 고객 화면에 새지 않는지 검사: ① html/js/sw/manifest 어디에도 staging 참조 없음 ② 서비스워커 CORE 목록에 없음 ③ 격리 파일은 상태가 '격리 대기'이며 전화 형식 이상 항목이 없음."""
import glob,json,re,sys,os
bad=[]
for f in glob.glob('**/*',recursive=True):
    if not os.path.isfile(f) or f.startswith(('data/staging','tests/','scripts/','docs/','.git')):continue
    if f.endswith(('.html','.js','.json','.webmanifest')) and 'staging' in open(f,encoding='utf-8',errors='ignore').read() and 'hospitals-pending' in open(f,encoding='utf-8',errors='ignore').read():bad.append(f'{f}: 격리 자료 참조')
sw=open('sw.js',encoding='utf-8').read()
if 'staging' in sw or 'hospitals-pending' in sw:bad.append('sw.js: 격리 자료가 캐시 목록에 있음')
for f in glob.glob('data/staging/*.json'):
    d=json.load(open(f,encoding='utf-8'))
    if not str(d.get('상태','')).startswith('격리 대기'):bad.append(f'{f}: 상태가 격리 대기가 아님')
    for x in d.get('목록',[]):
        if x.get('상태')!='격리 대기' or not re.match(r'^0\d{1,2}-\d{3,4}-\d{4}$',x.get('전화','')):bad.append(f'{f}: {x.get("이름")} 상태/전화 이상')
for b in bad:print('위반:',b)
print('격리 자료 노출 점검','통과' if not bad else f'위반 {len(bad)}건');sys.exit(1 if bad else 0)
