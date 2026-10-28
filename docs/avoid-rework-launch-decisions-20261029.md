# 효자 재작업 방지 및 출시 선행 결정표 v0.1
작성일 2026-10-29. 개인 프로젝트 / 용인 우선 / 전국 확장 보류.
운영 변경·개발자 계정 생성·결제·스토어 제출 없음.

## 출시 전 반드시 확정할 결정 (결정 전 외부 가입/비용 지출 보류)
1. Google Play 계정 유형: 건강/의료 앱 등 조직 등록 의무 카테고리 해당 여부를 실제 효자 기능·선언 카테고리 기준으로 검토. 공식 정책 https://support.google.com/googleplay/android-developer/answer/10788890
2. Apple 개인 vs 조직: 개인/개인사업자는 법적 이름이 판매자로 표시. 조직은 법인 실체·D-U-N-S 등 요구. https://developer.apple.com/kr/help/account/membership/program-enrollment
3. 사업화 시점 및 앱 소유권/브랜드·상표 검토. Apple 개인→조직 전환은 별도 심사 https://developer.apple.com/help/account/membership/updating-your-account-information
4. Google 개인→조직 전환은 공식 절차가 있지만 재확인 필요. 앱 이전 시 일부 테스트 그룹/설정은 다시 구성할 수 있음. https://support.google.com/googleplay/android-developer/answer/13634888 ; https://support.google.com/googleplay/android-developer/answer/6230247
5. 앱 기술방식: 웹 견본 소스와 배포 구성 확인 후 Android AAB, iOS 빌드 전략 결정. 앱 패키지 존재 확인 전 출시일 확정 금지.

## 개발 구조에서 재작업 줄이기
- 지역 선택/기관 데이터 모델은 전국 지역코드를 수용하되 실제 서비스는 용인만 노출.
- 의료 데이터 수집/검증/승인/공개 계층 분리, 변경 이력 및 원본 출처 보존.
- 앱 표시 모델과 내부 검증 스키마 분리. 미확인 기관은 '영업 중' 표기 금지.
- 패키지 ID/번들 ID, 앱 이름, 소유권, 서명 키 보관방식은 확정 후 고정.
- 개인정보/위치/사진/가족/워치 기능은 실제 구현·동의·삭제 정책 확인 후 선언.
- 빌드 및 검증 자동화는 시험 브랜치에서만 먼저 진행.

## 출시 게이트
A. 용인 공식 의료기관 운영상태 개별 교차검증과 예외 처리
B. Android/iOS 실제 기기 지도/전화/접근성/권한 테스트
C. 계정 유형 정책 적합성 확인 및 사용자 승인
D. 개인정보/의료 관련 고지·지원 연락처 및 스토어 메타데이터
E. 사용자 승인 후 빌드 제출, 심사 대응

## 현재 상태
완료: 재작업 방지 의사결정 문서, 공식 정책 링크 확보.
미완료: 실제 앱 기술방식 감사, 계정 카테고리 판정, 설치형 앱 빌드, 446건 기관별 운영상태 검증, 실제 기기 검수.
