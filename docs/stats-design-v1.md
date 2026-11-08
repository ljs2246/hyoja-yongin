# 효자 익명 이용 통계 설계 (시험 브랜치, 기본 꺼짐)

## 상태
- 코드: `footer.js` 맨 아래 모듈. **사이트 코드(`GC`)가 비어 있어 지금은 아무것도 보내지 않음.**
- 켜려면 대표 승인 → 효자 전용 GoatCounter 사이트 개설 → `GC`에 코드 입력 → 운영 반영(각각 별도 승인).

## 보내는 것 (허용 형식만, 코드와 검수기가 이중으로 강제)
| 이름 | 의미 | 예 |
|---|---|---|
| 주소 경로 | 화면 방문 1회 (검색어·해시 제외) | `/Emergency.html` |
| `search-<종류>-<구>-q0/1` | 검색 실행. 종류=pharmacy/emergency, 구=all/chein/giheung/suji, q=검색어 입력 여부(0/1) | `search-pharmacy-giheung-q1` |
| `tel-<화면>` | 전화 버튼 **눌렀다는 기록**(통화 연결 성공 아님) | `tel-centers` |
| `map-<종류>` | 지도 버튼 눌림 | `map-pharmacy` |
| `gu-<구>` | '지금 문 연 약국' 구 선택 | `gu-suji` |
| `size-<크기>` | 글자 크기 선택 | `size-large` |
- 화면 폭은 구간 값(320/360/390/430/600/768/1024/1440) 하나만 같이 보냄 → 모바일/PC 비율.

## 보내지 않는 것
검색어 글자, 전화번호, 기관 이름·주소, 위치(좌표), 이름, 건강정보, 쿠키·고유번호, 리퍼러(이전 주소).
검색어는 "입력했는지 여부(0/1)"만 쓴다.

## 지역별 이용량
- **사용자가 고른 구**(처인·기흥·수지)만 집계한다. 사용자 위치(IP·GPS)로 지역을 알아내지 않는다.
- GoatCounter가 자체적으로 보여 주는 국가·브라우저 통계는 서비스 쪽 기능이며, IP 원본은 저장하지 않는다고 공식 문서에 적혀 있음(아래 근거).

## 보내는 방식
- GoatCounter의 **추적 이미지(pixel)**: `https://<코드>.goatcounter.com/count?p=<이름>&e=true&s=<폭>,0,1&rnd=…` 하나만. 외부 스크립트(gc.zgo.at)는 불러오지 않음.
- `referrerPolicy=no-referrer`, 쿠키·localStorage 사용 없음.
- 브라우저의 추적 거부(Do Not Track / Global Privacy Control) 신호가 있으면 아무것도 안 보냄.
- 통계 서버가 막혀도 앱은 정상 동작(이미지 요청 실패는 무시).
- localhost에서는 꺼짐(개발 중 접속이 통계에 섞이지 않게). 시험용 설정은 localhost에서만 인정.

## 통합AI경영실 조회(효자 전용)
- 효자 전용 GoatCounter 사이트 코드 1개만 조회(아이랑 `airang-daejeon` 등 다른 사업 코드와 분리).
- 읽기 전용 키로 일·월 합계만 가져옴. 키 발급·연결은 대표 승인 후.

## GoatCounter 확인 근거 (2026-11-08, 공식 문서)
- 이용 조건: "free for reasonable public usage. … personal website or small-to-medium business … is fine, but … millions of pageviews/day isn't." (goatcounter.com/terms)
- 이벤트: 별도 속성이 없고 **이벤트 이름이 곧 경로(path)**. 맨 앞에 `/`를 쓰지 않음. (goatcounter.com/help/events)
- 추적 이미지: `p`(경로/이벤트 이름), `t`(제목), `e`(이벤트), `s`(화면 크기) 등을 받음. 리퍼러·화면 크기 일부는 기록 불가, 봇 요청이 늘 수 있음. (goatcounter.com/help/pixel)
- 개인정보: 개별 조회가 아닌 **집계 데이터**만 저장, IP·User-Agent 원본은 저장하지 않음, 세션 식별자는 메모리에서 8시간만 유지. (goatcounter.com/help/gdpr, /help/sessions)
- 이 문서들은 서비스 측 설명이며, 한국 개인정보보호법상 판단은 **법률 전문가 확인 필요**.

## 알려진 한계
- 이벤트 이름 방식이라 "어느 화면에서 검색했는지" 등 조합은 이름에 넣은 것만 볼 수 있음.
- 지역 지도(Regions.html)·견본(Review.html) 화면은 footer.js를 쓰지 않아 방문이 집계되지 않음(필요 시 추가).
- 이미지 방식은 봇 요청이 섞일 수 있고, 광고 차단 프로그램이 막을 수 있어 실제보다 적게 잡힐 수 있음.
