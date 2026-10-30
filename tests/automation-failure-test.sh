#!/bin/bash
# 실패 시나리오·복구 시험: 근거 없는 전화 링크를 임시 복사본에 넣어 자동 중단·알림이 되는지, 되돌리면 복구되는지 확인
set -u; cd "$(dirname "$0")/.."; ROOT=$PWD; TMP=$(mktemp -d); tar --exclude=.git --exclude=node_modules -cf - . | tar -xf - -C $TMP; cd $TMP; git init -q . ; git add -A >/dev/null; git -c user.email=t@t -c user.name=t commit -qm t; git checkout -qb test/failure-drill
OK=0
echo '<a href="tel:0319999999">미확인 기관 031-999-9999</a>' >> Welfare.html
python3 scripts/auto-run.py --out $TMP/runs >/tmp/drill1.log 2>&1; R1=$?
S1=$(ls $TMP/runs/ALERT-*.md 2>/dev/null | wc -l); NSTEP=$(python3 -c "import json,glob;print(len(json.load(open(glob.glob('$TMP/runs/run-*.json')[0]))['steps']))")
[ $R1 -ne 0 ] && [ $S1 -eq 1 ] && [ "$NSTEP" = "1" ] && echo "통과 실패 주입 시 첫 단계에서 자동 중단(이후 단계 미실행)·알림 파일 생성" || { echo "실패 자동 중단 시나리오"; OK=1; }
rm -rf $TMP/runs; git checkout -q -- Welfare.html
python3 scripts/auto-run.py --out $TMP/runs >/tmp/drill2.log 2>&1; R2=$?
[ $R2 -eq 0 ] && [ $(ls $TMP/runs/ALERT-*.md 2>/dev/null | wc -l) -eq 0 ] && echo "통과 원인 제거 후 재실행하면 전체 통과로 복구(알림 없음)" || { echo "실패 복구 시나리오"; OK=1; }
git checkout -q main 2>/dev/null || git checkout -qb main; python3 scripts/auto-run.py --out $TMP/runs2 >/tmp/drill3.log 2>&1; R3=$?
[ $R3 -ne 0 ] && grep -q "운영 main" /tmp/drill3.log && echo "통과 운영 main 브랜치에서는 자동 실행 거부" || { echo "실패 main 보호"; OK=1; }
rm -rf $TMP; exit $OK
