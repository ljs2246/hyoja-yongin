# 용인 응급의료기관·약국 자료를 공공데이터포털에서 받아 data/ 폴더에 저장합니다.
# 인증키는 환경변수 DATA_GO_KR_KEY 로만 읽고, 화면·기록에 절대 출력하지 않습니다.
import json, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

KEY = os.environ.get("DATA_GO_KR_KEY", "").strip()
BASE = "https://apis.data.go.kr/B552657"
GU = ["처인구", "기흥구", "수지구"]
KST = timezone(timedelta(hours=9))
OUT = os.path.join(os.path.dirname(__file__), "..", "data")

def call_page(path, params, page):
    q = {"serviceKey": KEY, "pageNo": str(page), "numOfRows": "200"}
    q.update(params)
    url = f"{BASE}/{path}?" + urllib.parse.urlencode(q, safe=":/")
    last = None
    for i in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                body = r.read()
            root = ET.fromstring(body)
            code = (root.findtext(".//resultCode") or "").strip()
            if code not in ("00", ""):
                raise RuntimeError("API 결과 코드 " + code + " " + (root.findtext(".//resultMsg") or ""))
            items = [{c.tag: (c.text or "").strip() for c in it} for it in root.iter("item")]
            total_text = root.findtext(".//totalCount")
            total = int(total_text) if total_text is not None else None
            if total is not None and total < 0:
                raise ValueError("invalid totalCount")
            return items, total
        except Exception as e:  # 키가 들어간 주소는 오류 문구에 넣지 않음
            last = "공공데이터 요청 실패 (" + type(e).__name__ + ")"
            time.sleep(3)
    raise RuntimeError(last)

def call(path, params):
    rows = []
    expected_total = None
    previous_page = None
    for page in range(1, 1001):
        items, total = call_page(path, params, page)
        if page == 1:
            expected_total = total
        elif total != expected_total:
            raise RuntimeError("조회 중 자료 건수가 바뀌어 기존 자료를 유지합니다.")
        if items and items == previous_page:
            raise RuntimeError("같은 페이지가 반복되어 기존 자료를 유지합니다.")
        rows.extend(items)
        if expected_total is not None:
            if len(rows) == expected_total:
                return rows
            if not items or len(rows) > expected_total:
                raise RuntimeError("전체 건수와 수집 건수가 달라 기존 자료를 유지합니다.")
        elif len(items) < 200:
            return rows
        previous_page = items
    raise RuntimeError("페이지 한도를 초과하여 기존 자료를 유지합니다.")

def fetch(path, label):
    rows = []
    for gu in GU:
        got = []
        for q1 in (f"용인시 {gu}", f"용인시{gu}"):
            got = call(path, {"Q0": "경기도", "Q1": q1})
            if got:
                break
        print(f"{label} {gu}: {len(got)}건")
        rows += got
    return rows

def main():
    os.makedirs(OUT, exist_ok=True)
    if not KEY:
        print("DATA_GO_KR_KEY 가 비어 있습니다.")
        with open(os.path.join(OUT, "status.json"), "w", encoding="utf-8") as f:
            json.dump({"상태": "실패", "이유": "인증키(DATA_GO_KR_KEY)를 찾지 못함"}, f, ensure_ascii=False, indent=1)
        sys.exit(1)
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M")
    status = {"확인한 때": now, "출처": "국립중앙의료원(공공데이터포털)"}
    ok = True
    for name, path, label in [
        ("emergency", "ErmctInfoInqireService/getEgytListInfoInqire", "응급의료기관"),
        ("pharmacy", "ErmctInsttInfoInqireService/getParmacyListInfoInqire", "약국"),
    ]:
        try:
            rows = fetch(path, label)
            if not rows:
                raise RuntimeError("0건")
            with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
                json.dump({"확인한 때": now, "건수": len(rows), "목록": rows}, f, ensure_ascii=False, indent=1)
            status[name] = {"상태": "성공", "건수": len(rows)}
        except Exception as e:
            ok = False
            status[name] = {"상태": "실패", "이유": str(e)[:200]}
            print(label, "실패:", str(e)[:200])
    with open(os.path.join(OUT, "status.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=1)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
