#!/bin/bash
# PR 방식 시험(로컬 모의, 가짜 gh 사용): DRY_RUN 은 push·PR·검사요청 0건, 실제 모드는 각 1건, 중복·이상자료·검사결과 없음 모두 안전하게 막힘
set -u; ROOT=$(cd "$(dirname "$0")/.." && pwd); T=$(mktemp -d); F=0
ok(){ echo "통과 $1"; }; ng(){ echo "실패 $1"; F=1; }
git init -q --bare $T/remote.git
cat > $T/remote.git/hooks/pre-receive <<'H'
#!/bin/bash
while read old new ref; do [ "$ref" = "refs/heads/main" ] && [ "$old" != "0000000000000000000000000000000000000000" ] && { echo "main 직접 push 금지(보호 규칙 모의)"; exit 1; }; done; exit 0
H
chmod +x $T/remote.git/hooks/pre-receive
mkdir $T/bin; cat > $T/bin/gh <<'G'
#!/bin/bash
echo "$*" >> "$GHLOG"
case "$1 $2" in
 "pr list") echo "${GH_OPEN:-0}";;
 "pr create") echo "https://example.invalid/pr/1";;
 "workflow run") [ "${GH_DISPATCH_FAIL:-0}" = 1 ] && exit 1; exit 0;;
 "api repos/"*) SHA=$(git rev-parse HEAD); f="$GH_SEQ_DIR/$(ls $GH_SEQ_DIR | sed -n "$(( $(cat $GH_SEQ_DIR/.n 2>/dev/null || echo 0)+1 ))p")"; n=$(cat $GH_SEQ_DIR/.n 2>/dev/null || echo 0); echo $((n+1)) > $GH_SEQ_DIR/.n; [ -f "$f" ] || f=$(ls -d $GH_SEQ_DIR/* | tail -1); sed "s/\"abc\"/\"$SHA\"/" "$f";;
esac
G
chmod +x $T/bin/gh; export PATH=$T/bin:$PATH GHLOG=$T/gh.log GITHUB_REPOSITORY=o/r
mkdir $T/w && cd $T/w && tar --exclude=.git --exclude=docs/runs -cf - -C $ROOT . | tar -xf - && git init -q . && git checkout -qb main && git add -A >/dev/null && git -c user.email=t@t -c user.name=t commit -qm base && git remote add origin $T/remote.git && git push -q origin main
BR="auto/data-$(TZ=Asia/Seoul date +%Y%m%d)"
chg(){ python3 - <<'P'
import json;d=json.load(open('data/pharmacy.json'));d['목록'][0]['dutyAddr']+=' (갱신)';json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)
P
}
reset(){ git checkout -q main; git reset -q --hard; git branch -q -D $BR 2>/dev/null; git push -q origin --delete $BR 2>/dev/null; : > $GHLOG; }
# 1 옛 방식은 보호된 main에서 차단
chg; git add data; git -c user.email=t@t -c user.name=t commit -qm old; git push -q origin main 2>/dev/null && ng "옛 방식 main 직접 push 통과" || ok "옛 방식(main 직접 push)은 보호 규칙에서 차단"
git reset -q --hard HEAD~1; : > $GHLOG
# 2 DRY_RUN=1: 원격 변화 0, gh 호출 0, 작업 폴더 복원
chg; BEFORE=$(git ls-remote origin | sort | md5sum)
DRY_RUN=1 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1
AFTER=$(git ls-remote origin | sort | md5sum)
[ "$BEFORE" = "$AFTER" ] && [ ! -s $GHLOG ] && git diff --cached --quiet && [ "$(git branch --show-current)" = main ] && grep -q "실제로는 아무것도 하지 않음" $T/o.txt && ok "DRY_RUN=1: 원격 변화 0, gh 호출 0(push·PR·검사요청 없음), 스테이징 복원" || { ng "DRY_RUN 안전"; cat $T/o.txt $GHLOG; }
# DRY_RUN 미지정도 기본 1
reset; chg; env -u DRY_RUN bash scripts/auto-data-pr.sh >/dev/null 2>&1; [ ! -s $GHLOG ] && ! git ls-remote --exit-code --heads origin $BR >/dev/null 2>&1 && ok "DRY_RUN 미지정 = 안전 모드(기본 1)" || ng "기본값이 안전하지 않음"
# 3 실제 모드: push 1, PR 1, qa 요청 1(브랜치 지정), main 불변, 검사 성공 확인
reset; chg; MAINSHA=$(git ls-remote origin refs/heads/main | cut -f1)
mkdir $T/seq1; cp tests/fixtures/checkruns/pending.json $T/seq1/1.json; cp tests/fixtures/checkruns/success.json $T/seq1/2.json
GH_SEQ_DIR=$T/seq1 MAX_TRIES=5 INTERVAL=0 DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1; RC=$?
git ls-remote --exit-code --heads origin $BR >/dev/null 2>&1 && ok "실제 모드: 갱신 브랜치 push" || ng "브랜치 push 안 됨"
[ "$(grep -c '^pr create' $GHLOG)" = 1 ] && ok "PR 정확히 1건" || ng "PR 건수"
grep -q "^workflow run qa-test-branch.yml --ref $BR" $GHLOG && [ "$(grep -c '^workflow run' $GHLOG)" = 1 ] && ok "필수 검사 qa 를 갱신 브랜치 지정으로 1회 요청" || ng "qa 요청"
[ "$(git ls-remote origin refs/heads/main | cut -f1)" = "$MAINSHA" ] && ok "main 불변" || ng "main 변경됨"
[ $RC = 0 ] && grep -q "통과: 필수 검사 qa 성공" $T/o.txt && ok "진행 중 → 성공 순서를 기다려 통과 확인" || { ng "검사 확인"; cat $T/o.txt; }
# 4 같은 날 재실행: 원격에 브랜치 있음 → 추가 push·PR·요청 0
: > $GHLOG; git checkout -q main; chg; DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1
grep -q "중복 방지" $T/o.txt && ! grep -q '^pr create\|^workflow run' $GHLOG && ok "같은 날 재실행: 중복 PR·검사요청 0건" || { ng "중복 방지"; cat $T/o.txt; }
# 5 열린 갱신 PR 이 이미 있으면 새로 만들지 않음
reset; chg; GH_OPEN=1 DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1
grep -q "열린 갱신 PR" $T/o.txt && ! git ls-remote --exit-code --heads origin $BR >/dev/null 2>&1 && ok "열린 PR 있으면 새 브랜치·PR 없음" || ng "열린 PR 중복"
# 6 이상 자료(급감)는 복구, 올리지 않음
reset; python3 - <<'P'
import json;d=json.load(open('data/pharmacy.json'));d['목록']=d['목록'][:3];d['건수']=3;json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)
P
DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1; git diff --quiet HEAD -- data/pharmacy.json && ! git ls-remote --exit-code --heads origin $BR >/dev/null 2>&1 && ! grep -q '^pr create' $GHLOG && ok "이상 자료는 복구되고 브랜치·PR 없음" || { ng "이상 자료 차단"; cat $T/o.txt; }
# 7 검사 결과가 끝내 없으면 실패(병합 금지)로 끝남(제한 횟수 후 중단)
reset; chg; mkdir $T/seq2; cp tests/fixtures/checkruns/none.json $T/seq2/1.json
GH_SEQ_DIR=$T/seq2 MAX_TRIES=3 INTERVAL=0 DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1; RC=$?
[ $RC != 0 ] && grep -q "병합 금지 유지" $T/o.txt && [ "$(grep -c '^api' $GHLOG)" = 3 ] && ok "검사 결과 없음 → 3회만 확인 후 실패 종료(병합 금지, 무한 대기 없음)" || { ng "결과 없음 처리"; cat $T/o.txt; }
# 8 검사 실패 → 즉시 중단·실패
reset; chg; mkdir $T/seq3; cp tests/fixtures/checkruns/failure.json $T/seq3/1.json
GH_SEQ_DIR=$T/seq3 MAX_TRIES=5 INTERVAL=0 DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1; RC=$?
[ $RC != 0 ] && [ "$(grep -c '^api' $GHLOG)" = 1 ] && ok "검사 실패 → 기다리지 않고 실패(병합 금지)" || { ng "검사 실패 처리"; cat $T/o.txt; }
# 9 qa 실행 요청 자체가 실패하면 실패로 끝남
reset; chg; GH_DISPATCH_FAIL=1 DRY_RUN=0 bash scripts/auto-data-pr.sh >$T/o.txt 2>&1; RC=$?
[ $RC != 0 ] && grep -q "병합 금지 상태 유지" $T/o.txt && ok "검사 요청 실패 → 병합 금지 유지" || ng "요청 실패 처리"
# 10 지역 흐름(PATHS/PREFIX/CHECK=none)도 같은 안전 규칙
reset; python3 - <<'P'
import json,os
p='data/regions-status.json'
d=json.load(open(p)) if os.path.exists(p) else {}
d['시험']=1;json.dump(d,open(p,'w'),ensure_ascii=False)
P
RB="auto/regions-$(TZ=Asia/Seoul date +%Y%m%d)"
PREFIX=auto/regions PATHS="data/regions-status.json data/regions-source.json" CHECK=none DRY_RUN=1 bash scripts/auto-data-pr.sh >/dev/null 2>&1
[ ! -s $GHLOG ] && ! git ls-remote --exit-code --heads origin $RB >/dev/null 2>&1 && ok "지역 갱신 흐름도 DRY_RUN=1 이면 push·PR 0건" || ng "지역 흐름 DRY_RUN"
cd /; rm -rf $T; exit $F
