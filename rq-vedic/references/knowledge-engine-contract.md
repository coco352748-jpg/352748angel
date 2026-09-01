# RQ Vedic AI 데이터베이스·빅데이터 지식엔진 계약

`CONTRACT_ID=RQ_VEDIC_KNOWLEDGE_ENGINE_V1`

## 목적

베딕·조티시 자료의 양을 곧바로 규칙의 권위로 바꾸지 않고, 원문·방법·규칙·반례·차트 적용·최종 주장까지 역추적 가능한 지식엔진을 만든다. 이 엔진은 `$rq-vedic` 내부 하위 메뉴의 공통 Source 기반이며 별도 독립 스킬이 아니다.

`AI 빅데이터 = 대량 자료를 찾고 비교하는 증거 후보 풀`

`AI 데이터베이스 = 검증된 Source·방법·규칙·예외·적용범위를 구조화한 권위 원장`

빅데이터의 빈도·검색순위·임베딩 유사도는 입장권이 아니다. 최종 주장에는 반드시 정확한 Source passage와 방법·적용조건이 연결돼야 한다.

## 1. 네 저장층

### A. RAW_CORPUS_LAKE

원문을 수정하지 않고 보존한다.

- 고전 원문·판본·번역본
- 현대 공식 curriculum·certification·기술문서
- 저자 공식 기술자료
- 사용자가 승인한 프로젝트 Source
- 표·차트·스크린샷·OCR 결과와 원본 locator

필수 필드:

`document_id, version_id, source_family_id, title, author_or_institution, edition, language, publication_date, acquired_at, canonical_url_or_locator, content_hash, rights_scope, raw_state`

OCR·번역·정규화는 원본을 덮지 않는다. 각각 `TRANSFORMATION_RECORD`로 만들어 입력 hash·출력 hash·도구·설정·수정이력을 남긴다.

### B. EVIDENCE_DATABASE

Source passage와 규칙 후보를 분리한다.

1. `SOURCE_FAMILY`: 같은 원문을 재전재한 자료를 한 계보로 묶는다.
2. `PASSAGE`: 문서의 exact 장·절·페이지·문단·표·셀 locator.
3. `METHOD`: ayanamsa·zodiac·house system·계산식·적용질문·예외.
4. `CLAIM`: passage가 실제로 말하는 최소 주장.
5. `RULE_CARD`: 여러 claim을 비교해 만든 적용 가능한 규칙.
6. `EXCEPTION_CARD`: 규칙의 취소·제한·비적용·학파충돌.
7. `ADMISSION_RECORD`: 현재 Target에서의 입장등급과 판정근거.

`RULE_CARD` 최소 필드:

```text
rule_id
canonical_claim
source_claim_refs[]
source_family_refs[]
method_id
applicable_d_charts[]
applicable_houses[]
applicable_modules[]
required_inputs[]
calculation_settings[]
exceptions[]
falsifiers[]
admission_grade
evidence_authority
state
version
supersedes
```

### C. CASE_AND_COUNTEREXAMPLE_BANK

규칙이 실제 차트 packet에서 어떻게 작동하고 어디서 멈추는지 검증한다.

- `WORKED_EXAMPLE`: 계산설정과 정답경로가 확인된 예제
- `COUNTEREXAMPLE`: 규칙이 성립하지 않거나 경계가 드러난 사례
- `REGRESSION_CASE`: 스킬 수정 뒤에도 같은 경계·판정이 유지돼야 하는 테스트
- `USER_CHART_CASE`: 현재 사용자 Target에만 귀속되는 실행기록

필수 필드:

`case_id, case_type, chart_input_ref, calculation_setting_ref, target, expected_direct_facts, applicable_rule_refs, nonmatching_rule_refs, observed_layer_outputs, exceptions, adjudication, privacy_scope, state`

사용자 개인차트 사례를 일반 법칙으로 자동 승격하지 않는다. 한 사례의 적중·부적중을 전체 조티시 규칙의 증명·반증으로 확대하지 않는다.

### D. RUNTIME_AND_AUDIT_LEDGER

한 실행이 어떤 Source·규칙·메뉴·층·에이전트를 거쳤는지 기록한다.

`target_lock, source_snapshot, selected_level, selected_d_chart, selected_house, selected_modules, method_bindings, layer_packets, operator_results, admitted_claims, filtered_claims, holds, conflicts, final_claims, qa, execution_hash`

동일 실행을 다시 검산할 수 있도록 Source와 규칙의 version을 고정한다. 최신 규칙이 생겨도 과거 실행 packet을 조용히 다시 쓰지 않는다.

## 2. 독립 권한축

다음 축을 하나의 점수로 합치지 않는다.

### Source class

- `USER_CANONICAL_SOURCE`
- `PRIMARY_CLASSICAL_TEXT`
- `OFFICIAL_MODERN_CURRICULUM`
- `OFFICIAL_TECHNICAL_DOCUMENT`
- `SCHOLAR_TECHNICAL_WORK`
- `SECONDARY_EXPLANATION`
- `INFERENCE`

### Method admission

- `CURRENT_COMMON_CORE`
- `METHOD_SPECIFIC`
- `POST_CHART_SCHOLAR`
- `HISTORICAL_SUPPORT`
- `HOLD`

### Evidence authority

- `DIRECT_SOURCE`
- `DERIVED`
- `REFERENCE`
- `USER_SPECIFIED`
- `INFERENCE`
- `WORKING_ASSUMPTION`

### Data state

- `ACTIVE`
- `VOID`
- `NONE`
- `NOT_PARSED`
- `NOT_APPLICABLE`
- `CONFLICT`
- `HOLD`

`PRIMARY_CLASSICAL_TEXT`라는 Source class만으로 `CURRENT_COMMON_CORE`가 되지 않는다. `CURRENT_COMMON_CORE`는 현재 복수 독립 계보·재현성·방법 무충돌 게이트를 별도로 통과해야 한다.

## 3. 빅데이터 수집·정제 route

정확한 순서:

`수집 → 원본 hash·locator 잠금 → OCR/번역 분리 → passage 분할 → 동일 Source family 중복제거 → 용어·방법 태깅 → claim 최소단위 추출 → 규칙후보 생성 → 대조·예외·반례 탐색 → 방법별 분리 → 사람/권위 게이트 검토 → RULE_CARD 활성화 → 회귀사례 검증 → 버전 고정`

다음은 금지한다.

- 검색결과 제목만 읽고 규칙 생성
- 여러 재전재 페이지를 복수 독립 근거로 계산
- 다수 문서의 반복문장을 합의나 진실로 자동 승격
- 번역문을 원문과 동일한 직접권위로 표시
- 서로 다른 ayanamsa·house system·aspect·dasha·yoga 체계를 평균화
- Source가 없는 빈칸을 AI 일반지식으로 보충
- 반례를 제거해 규칙 적용률을 높이는 행위

## 4. 규칙 승급 상태기계

규칙은 다음 상태를 거친다.

`RAW_CLAIM → PARSED_CLAIM → RULE_CANDIDATE → METHOD_BOUND → EVIDENCE_REVIEWED → CASE_TESTED → ACTIVE_RULE`

병렬 종료상태:

- `HOLD`: Source·방법·Target 결속 부족
- `CONFLICT`: 동등 권위 claim 충돌
- `REJECTED`: 원문 오독·중복근거·반례 실패·범위 불일치
- `VOID`: 사용자 또는 정본 권위가 사용금지
- `SUPERSEDED`: 새 version이 대체하되 과거 version 보존

AI는 `RULE_CANDIDATE`까지 자동 제안할 수 있다. `ACTIVE_RULE` 승격에는 passage·방법·예외·재현사례·입장등급이 모두 닫혀야 한다. 빈도나 모델 자신감은 승격조건이 아니다.

## 5. 차트별 규칙 컴파일

차트별 스킬은 파일을 20개 복제하는 방식이 아니라 하나의 규칙원장에서 exact scope를 컴파일한다.

```text
LEVEL
× ACTION
× D_CHART
× HOUSE
× MODULE
× METHOD_BINDING
× SOURCE_SNAPSHOT
= ONE EXECUTION JOB
```

각 D-chart 규칙에는 최소한 다음이 있어야 한다.

- `DOMAIN_OBJECT`: 이 차트가 어떤 현실 Object를 설명하는가
- `BASE_ANCHOR`: Lagna·Rashi·Bhava·reference 기준
- `HOUSE_TRANSLATION`: 1H~12H의 해당 D-domain 번역
- `ACTOR_RULES`: Lord·Occupant·Dispositor·Co-field·Support 권한
- `METHOD_DEPENDENCIES`: 계산·학파·Source 설정
- `LAYER_BOUNDARIES`: 구조·강도·시간·귀속의 설명범위
- `EXCEPTIONS_AND_FALSIFIERS`
- `HANDOFF`: 다음 19층에 넘길 값과 넘기지 못할 주장

20D 공통문장을 복사해 차트명만 바꾸지 않는다. 공통 규칙은 공유하되 D-domain·House translation·적용조건은 독립 record로 유지한다.

## 6. 검색과 AI 사용 경계

- 키워드·전문검색·벡터검색은 후보 passage를 찾는 도구다.
- 검색 hit는 `PASSAGE` exact locator를 다시 읽은 뒤에만 근거가 된다.
- 요약모델은 claim 후보를 만들 수 있으나 Source 문장의 범위·강도·예외를 줄이지 못한다.
- 규칙 생성모델과 검증모델은 같은 출력만 서로 확인하는 구조로 두지 않는다. 검증은 원문·반례·방법·case packet을 다시 본다.
- 최종 해석모델은 ACTIVE_RULE과 현재 chart Source만 사용한다. raw corpus의 유사문장을 직접 끌어와 확정문을 만들지 않는다.

## 7. 저장 배치 원칙

Git에는 스키마·레지스트리·활성 RULE_CARD·검증기·manifest·hash를 둔다. 대용량 PDF·이미지·OCR 원문은 승인된 대용량 저장소에 두고 Git에는 immutable locator와 hash만 둔다.

권장 논리 배치:

```text
rq-vedic/
  references/
    vedic-submenu-registry.json
    knowledge-engine-contract.md
    analysis-operator-contract.md
    fna98-end-gate.md
  schemas/
    source.schema.json
    rule-card.schema.json
    case.schema.json
    execution.schema.json
  data/
    source-family-registry.jsonl
    active-rule-ledger.jsonl
    conflict-ledger.jsonl
    case-manifest.jsonl
  scripts/
    validate_vedic_submenu.py
```

이 배치는 최종 구현 목표다. 빈 placeholder나 Source 없는 RULE_CARD를 만들어 완료로 가장하지 않는다.

## 8. 완료 판정

### 설계 완료

메뉴·데이터모델·승급상태·권위축·중복방지·실행 packet·FNa98 게이트가 서로 모순 없이 닫히고 검증기가 통과한 상태다.

### 데이터베이스 완료

요청된 Source 범위 전체가 hash·locator·passage·method·claim으로 구조화되고 누락·충돌 ledger가 닫힌 상태다.

### 규칙 스킬 완료

요청된 D-chart·House·Module의 ACTIVE_RULE·예외·case test·ELIVEDIC→ELICOLLEGE→ELIPHD 출력계약이 모두 실행 검증된 상태다.

설계 완료를 데이터베이스·규칙 corpus 완료로 승격하지 않는다. 후자의 Source가 아직 없으면 `IN_PROGRESS` 또는 정확한 국소 `HOLD`다.
