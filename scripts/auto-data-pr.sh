#!/bin/bash
# 공식정보 자동 갱신 → 검증 후 PR 방식(운영 main에 직접 올리지 않음). 지시 013.
# 순서: 자료 검사(이상하면 이전 승인본으로 복구) → 바뀐 게 없으면 종료 → 날짜별 갱신 브랜치에 커밋·푸시 → (DRY_RUN=0 일 때만) PR 생성.
# 중복 방지: 같은 날짜 브랜치가 이미 원격에 있으면 아무것도 만들지 않는다. 사용: DRY_RUN=1 scripts/auto-data-pr.sh
set -u; DRY_RUN=${DRY_RUN:-1}; BASE=${BASE:-main}; DAY=$(TZ=Asia/Seoul date +%Y%m%d); BR="auto/data-$DAY"
python3 scripts/check-data.py --restore || exit 1
git add data/emergency.json data/pharmacy.json data/status.json 2>/dev/null
git diff --cached --quiet && { echo "변경 없음: 아무것도 만들지 않음"; exit 0; }
if git ls-remote --exit-code --heads origin "$BR" >/dev/null 2>&1; then echo "중복 방지: $BR 이미 있음 → 건너뜀"; git reset -q; exit 0; fi
git checkout -q -b "$BR" && git -c user.name="자동 갱신" -c user.email="actions@users.noreply.github.com" commit -qm "자동 갱신(검증 통과): 병원·약국 자료 $DAY" || exit 1
git push -q origin "$BR" || { echo "푸시 실패(보호 규칙·권한 확인)"; exit 1; }
if [ "$DRY_RUN" = "1" ]; then echo "DRY_RUN: 브랜치 $BR 만 올림, PR은 만들지 않음"; exit 0; fi
gh pr list --head "$BR" --state open --json number --jq 'length' | grep -qx 0 || { echo "중복 방지: 열린 PR 이미 있음"; exit 0; }
gh pr create --base "$BASE" --head "$BR" --title "자동 갱신: 병원·약국 자료 $DAY (검증 통과, 승인 대기)" --body "자료 검사 관문을 통과한 변경입니다. 피트 검수 후 병합. 자동 병합 없음."
