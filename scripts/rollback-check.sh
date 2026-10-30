#!/bin/bash
# 이전 정상 버전 복구 "검증" 절차. 어떤 브랜치도 옮기거나 덮어쓰지 않는다(읽기 전용 확인).
# 1) 실행 기록 중 '전체 통과'였던 가장 최근 커밋을 찾는다  2) 그 커밋을 임시 폴더에 내려받아 전체 검사를 다시 통과하는지 확인한다.
# 실제 되돌리기(운영 main 포함)는 피트 검수 + 준식님 승인 후에만 사람이 수행한다. 사용: rollback-check.sh [기록폴더]
set -u; RUNS=${1:-docs/runs}
SHA=$(python3 - "$RUNS" <<'P'
import json,glob,sys
ok=[json.load(open(f)) for f in sorted(glob.glob(sys.argv[1]+'/run-*.json'))]
ok=[j for j in ok if j.get('status')=='전체 통과' and j.get('commit') not in(None,'unknown')]
print(ok[-1]['commit'] if ok else '')
P
)
[ -z "$SHA" ] && { echo "복구 후보 없음: 통과 기록이 없습니다"; exit 1; }
echo "복구 후보(마지막 정상 커밋): $SHA"
WT=$(mktemp -d); git worktree add -q --detach "$WT" "$SHA" || { echo "후보 커밋을 내려받지 못했습니다"; exit 1; }
( cd "$WT" && python3 scripts/auto-run.py --out "$WT/.rollback-runs" ) ; RC=$?
git worktree remove --force "$WT"
[ $RC -eq 0 ] && echo "복구 후보 검증 통과 → 되돌리기는 승인 후 수동 수행(자동 실행 안 함)" || echo "복구 후보 검증 실패 → 더 이전 기록 확인 필요"
exit $RC
