#!/usr/bin/env python3
"""병합 게이트 판정(실패 시 닫힘): 같은 커밋(sha)에 대해 check run 'qa' 가 '성공'일 때만 통과.
결과 없음·진행 중·실패·취소·다른 커밋의 결과는 모두 '병합 금지'. 입력: GitHub check-runs API JSON 파일(또는 -), 인자: sha. 종료코드 0=통과, 1=금지."""
import json,sys
sha=sys.argv[2] if len(sys.argv)>2 else '';src=sys.argv[1]
try:d=json.load(sys.stdin if src=='-' else open(src))
except Exception:print('병합 금지: 검사 결과를 읽을 수 없음');sys.exit(1)
runs=[r for r in d.get('check_runs',[]) if r.get('name')=='qa' and r.get('head_sha')==sha]
if not runs:print('병합 금지: 이 커밋의 필수 검사 qa 결과가 없음');sys.exit(1)
r=max(runs,key=lambda x:x.get('started_at') or '')
if r.get('status')!='completed':print('병합 금지: 검사가 아직 진행 중');sys.exit(1)
if r.get('conclusion')!='success':print('병합 금지: 검사 결과 '+str(r.get('conclusion')));sys.exit(1)
print('통과: 필수 검사 qa 성공');sys.exit(0)
