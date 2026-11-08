#!/usr/bin/env python3
"""보안 검사: 비밀정보 흔적, 외부 스크립트, 위험 링크, 워크플로우 권한. 실패 시 종료코드 1."""
import re,glob,sys,os
bad=[]
SECRET=[r'AKIA[0-9A-Z]{16}',r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',r'ghp_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'xox[baprs]-[A-Za-z0-9-]{10,}',r'AIza[0-9A-Za-z_\-]{35}',r'ya29\.[0-9A-Za-z_\-]{20,}',r'(?i)(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*["\'][^"\']{12,}["\']']
files=[f for f in glob.glob('**/*',recursive=True) if os.path.isfile(f) and not f.startswith(('.git/','node_modules/')) and f.endswith(('.html','.js','.json','.py','.sh','.yml','.md','.cjs','.css','.webmanifest'))]
for f in files:
    s=open(f,errors='ignore').read()
    for p in SECRET:
        m=re.search(p,s)
        if m and not (f.startswith('tests/') or os.path.basename(f).startswith('test_') or '/test' in f): bad.append((f,'비밀정보 의심: '+m.group(0)[:12]+'…'))
for f in glob.glob('*.html'):
    s=open(f).read()
    for m in re.finditer(r'<script[^>]+src="(https?:)?//([^"/]+)',s): bad.append((f,'외부 스크립트: '+m.group(2)))
    for m in re.finditer(r'<a [^>]*target="_blank"[^>]*>',s):
        if 'noopener' not in m.group(0): bad.append((f,'target=_blank 에 rel=noopener 없음'))
    if re.search(r'\beval\(|document\.write\(',s): bad.append((f,'eval/document.write 사용'))
for f in glob.glob('.github/workflows/*.yml'):
    s=open(f).read()
    if 'permissions:' not in s: bad.append((f,'permissions 미지정(최소 권한 명시 필요)'))
    if re.search(r'permissions:\s*write-all',s): bad.append((f,'write-all 금지'))
    if 'qa-test-branch' in f and re.search(r'contents:\s*write',s): bad.append((f,'검수 워크플로우에 코드 쓰기 권한 금지'))
for f,m in bad:print('보안 검사 실패:',f,m)
print('보안 검사','통과' if not bad else f'실패 {len(bad)}건');sys.exit(1 if bad else 0)
