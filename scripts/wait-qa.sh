#!/bin/bash
# 필수 검사 qa 결과를 제한 횟수만 확인(무한 대기 금지). 통과가 아니면 PR에 '병합 금지' 안내를 남기고 실패로 끝낸다.
# 환경변수: MAX_TRIES(기본 40) INTERVAL(기본 30초) → 최대 약 20분
set -u; SHA=$1; MAX=${MAX_TRIES:-40}; IV=${INTERVAL:-30}; REPO=${GITHUB_REPOSITORY:-}; T=$(mktemp)
for i in $(seq 1 $MAX); do
  gh api "repos/$REPO/commits/$SHA/check-runs" > "$T" 2>/dev/null
  if python3 "$(dirname "$0")/pr-gate-check.py" "$T" "$SHA" >/tmp/gate.$$ 2>&1; then cat /tmp/gate.$$; rm -f "$T" /tmp/gate.$$; exit 0; fi
  grep -q "진행 중\|결과가 없음" /tmp/gate.$$ || { cat /tmp/gate.$$; break; }   # 실패·취소는 기다리지 않고 종료
  sleep $IV
done
cat /tmp/gate.$$ 2>/dev/null; echo "검사 통과를 확인하지 못함 → 병합 금지 유지"; rm -f "$T" /tmp/gate.$$; exit 1
