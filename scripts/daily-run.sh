#!/bin/bash
# 일일 자동 실행(운영 main 불변): 테스트 브랜치를 임시 폴더로 내려받아 검사하고, 기록은 저장소 밖 LOG_DIR에 보존한다.
# 어떤 push·merge·배포도 하지 않는다. 시작/종료 시점의 origin/main 커밋이 같지 않으면 실패 처리.
# 환경변수: BRANCH(기본 test/yongin-pilot-prep-v2) LOG_DIR(기본 ~/hyoja-run-logs) KEEP_DAYS(기본 90)
set -u
BRANCH=${BRANCH:-test/yongin-pilot-prep-v2}; LOG_DIR=${LOG_DIR:-$HOME/hyoja-run-logs}; KEEP_DAYS=${KEEP_DAYS:-90}
REPO=${REPO:-$(cd "$(dirname "$0")/.." && pwd)}
mkdir -p "$LOG_DIR"; DAY=$(TZ=Asia/Seoul date +%Y-%m-%d_%H%M)
cd "$REPO" || exit 2
git fetch -q origin '+refs/heads/*:refs/remotes/origin/*' || { echo "중단: 원격 가져오기 실패" | tee "$LOG_DIR/ALERT-$DAY.txt"; exit 2; }
MAIN_BEFORE=$(git rev-parse origin/main)
WT=$(mktemp -d); git worktree add -q --detach "$WT" "origin/$BRANCH" || { echo "중단: 브랜치 없음 $BRANCH" | tee "$LOG_DIR/ALERT-$DAY.txt"; exit 2; }
( cd "$WT" && git checkout -q --detach && python3 scripts/auto-run.py --out "$LOG_DIR/runs-$DAY" ) > "$LOG_DIR/daily-$DAY.log" 2>&1; RC=$?
git worktree remove --force "$WT"
MAIN_AFTER=$(git rev-parse origin/main)
if [ "$MAIN_BEFORE" != "$MAIN_AFTER" ]; then echo "경고: 실행 중 origin/main 이 바뀜(우리 실행은 main을 쓰지 않음)" >> "$LOG_DIR/daily-$DAY.log"; fi
[ $RC -ne 0 ] && echo "일일 실행 실패 $DAY 브랜치 $BRANCH 종료코드 $RC (로그: daily-$DAY.log)" > "$LOG_DIR/ALERT-$DAY.txt"
find "$LOG_DIR" -type f -mtime +"$KEEP_DAYS" -delete 2>/dev/null; find "$LOG_DIR" -mindepth 1 -type d -empty -delete 2>/dev/null
echo "일일 실행 종료코드 $RC / main 불변: $([ "$MAIN_BEFORE" = "$MAIN_AFTER" ] && echo 예 || echo 아니오) / 기록: $LOG_DIR/daily-$DAY.log"
exit $RC
