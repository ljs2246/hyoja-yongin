#!/usr/bin/env python3
"""고령친화·접근성 정적 검사(자동 가능한 최소 기준): lang, viewport, title, img alt, 입력 라벨, 글자 크기 확대 허용(user-scalable=no 금지), 전화 링크 이름."""
import re,glob,sys
bad=[]
for f in sorted(glob.glob('*.html')+glob.glob('lab/**/*.html',recursive=True)):
    s=open(f).read()
    if f in('Guide.html',) and '<html' not in s: continue
    if '<html' not in s: continue
    if not re.search(r'<html[^>]+lang="ko"',s): bad.append((f,'html lang="ko" 없음'))
    if 'name="viewport"' not in s: bad.append((f,'viewport 없음'))
    elif re.search(r'user-scalable\s*=\s*no|maximum-scale\s*=\s*1(\.0)?\b',s): bad.append((f,'확대 금지 설정'))
    if not re.search(r'<title>[^<]+</title>',s): bad.append((f,'title 없음'))
    for m in re.finditer(r'<img\b[^>]*>',s):
        if 'alt=' not in m.group(0): bad.append((f,'img alt 없음'))
    for m in re.finditer(r'<input\b[^>]*>',s):
        t=m.group(0)
        if 'type="hidden"' in t or 'type="submit"' in t or 'type="button"' in t:continue
        if not re.search(r'aria-label=|id="[^"]+"',t): bad.append((f,'input 라벨 연결 없음'))
    for m in re.finditer(r'<a [^>]*href="tel:[^"]*"[^>]*>(.*?)</a>',s,re.S):
        if not re.sub(r'<[^>]+>','',m.group(1)).strip(): bad.append((f,'이름 없는 전화 링크'))
for f,m in bad:print('접근성 검사 실패:',f,m)
print('접근성 검사','통과' if not bad else f'실패 {len(bad)}건');sys.exit(1 if bad else 0)
