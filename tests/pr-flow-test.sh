#!/bin/bash
# PR 방식 전환 시험(로컬 모의): main 직접 push는 막고 갱신 브랜치 push는 허용하는 원격에서 ①옛 방식 실패 ②새 방식 성공 ③재실행 중복 0 ④이상 자료는 저장 안 됨 을 확인
set -u; ROOT=$(cd "$(dirname "$0")/.." && pwd); T=$(mktemp -d); OK=0
git init -q --bare $T/remote.git
cat > $T/remote.git/hooks/pre-receive <<'H'
#!/bin/bash
while read old new ref; do [ "$ref" = "refs/heads/main" ] && [ "$old" != "0000000000000000000000000000000000000000" ] && { echo "main 직접 push 금지(보호 규칙 모의)"; exit 1; }; done; exit 0
H
chmod +x $T/remote.git/hooks/pre-receive
mkdir $T/w && cd $T/w && tar --exclude=.git --exclude=docs/runs -cf - -C $ROOT . | tar -xf - && git init -q . && git checkout -qb main && git add -A >/dev/null && git -c user.email=t@t -c user.name=t commit -qm base && git remote add origin $T/remote.git
# 보호 모의를 켜기 전에 최초 main 생성은 old=0000 이라 통과
git push -q origin main
python3 - <<'P'
import json;d=json.load(open('data/pharmacy.json'));d['목록'][0]['dutyAddr']+=' (갱신)';json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)
P
git add data && git -c user.email=t@t -c user.name=t commit -qm "옛 방식: main 직접 갱신" && { git push -q origin main 2>/dev/null && { echo "실패 옛 방식이 보호된 main에서도 통과함"; OK=1; } || echo "통과 옛 방식(main 직접 push)은 보호 규칙에서 차단됨 → 전환 필요"; }
git reset -q --hard HEAD~1
python3 - <<'P'
import json;d=json.load(open('data/pharmacy.json'));d['목록'][0]['dutyAddr']+=' (갱신)';json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)
P
DRY_RUN=1 bash scripts/auto-data-pr.sh >$T/o1.txt 2>&1; git ls-remote --exit-code --heads origin "auto/data-$(TZ=Asia/Seoul date +%Y%m%d)" >/dev/null 2>&1 && echo "통과 새 방식: 갱신 브랜치 push 성공, main 불변" || { echo "실패 새 방식 push"; OK=1; }
git checkout -q main; python3 - <<'P'
import json;d=json.load(open('data/pharmacy.json'));d['목록'][0]['dutyAddr']+=' (갱신)';json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)
P
DRY_RUN=1 bash scripts/auto-data-pr.sh >$T/o2.txt 2>&1; grep -q "중복 방지" $T/o2.txt && echo "통과 같은 날 재실행 시 중복 브랜치·PR 0건" || { echo "실패 중복 방지"; cat $T/o2.txt; OK=1; }
git checkout -q -- data 2>/dev/null; git reset -q --hard; git checkout -q main
python3 - <<'P'
import json;d=json.load(open('data/pharmacy.json'));d['목록']=d['목록'][:3];d['건수']=3;json.dump(d,open('data/pharmacy.json','w'),ensure_ascii=False)
P
git checkout -q -b scratch; git branch -q -D "auto/data-$(TZ=Asia/Seoul date +%Y%m%d)" 2>/dev/null; git push -q origin --delete "auto/data-$(TZ=Asia/Seoul date +%Y%m%d)" 2>/dev/null
DRY_RUN=1 bash scripts/auto-data-pr.sh >$T/o3.txt 2>&1
git diff --quiet HEAD -- data/pharmacy.json && ! git ls-remote --exit-code --heads origin "auto/data-$(TZ=Asia/Seoul date +%Y%m%d)" >/dev/null 2>&1 && echo "통과 이상 자료(급감)는 복구되어 브랜치·PR로 올라가지 않음" || { echo "실패 이상 자료 차단"; cat $T/o3.txt; OK=1; }
cd /; rm -rf $T; exit $OK
