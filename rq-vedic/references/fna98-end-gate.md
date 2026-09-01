# RQ Vedic FNa98 처음부터 엔딩까지 종결 게이트

`CONTRACT_ID=RQ_VEDIC_FNA98_END_GATE_V1`

## 최종 목적

`사용자 질문 → 잠긴 Source와 방법 → 정확한 Vedic 하위 메뉴 → ELIVEDIC → ELICOLLEGE → ELIPHD → 최종 답 → 역검산 가능한 FNa98 결과`

설계가 깊다는 이유로 실행 완료를 선언하지 않는다. 데이터가 많다는 이유로 규칙이 확인됐다고 선언하지 않는다. 19층이 존재한다는 이유로 현재 Target에 전부 적용됐다고 선언하지 않는다.

## 0. Target Gate

다음을 잠근다.

`ACTUAL_QUESTION, ACTION, SUBJECT, RESULT_OBJECT, D_CHART, HOUSE, MODULES, LEVEL, TIME_SCOPE, SOURCE_SCOPE, METHOD_SCOPE, OUTPUT, EXCLUSIONS`

- 가장 최근 사용자 질문이 모든 과거 명령보다 우선한다.
- Selector만 있으면 메뉴 탐색상태이며 자동 실행하지 않는다.
- 한 D-chart가 12H 전체를, 한 House가 20D 전체를 자동 개방하지 않는다.
- `20D×12H=240`은 명시 요청에서만 Job을 생성한다.

## 1. Source Gate

모든 입력을 다음 중 하나로 분류한다.

- chart actual value
- general rule Source
- method/calculation Source
- worked case
- user correction
- inference

Source에는 `id, version, hash, locator, authority, state`가 있어야 한다. 동일 `evidence_key`는 한 번만 센다. Source가 없으면 유사 자료·기억·AI 지식으로 채우지 않는다.

통과조건:

- 사용된 직접값이 exact Source로 돌아감
- 일반규칙과 개인차트값이 분리됨
- OCR·번역·DERIVED 변환이 원본과 분리됨
- 충돌·미파싱·NONE·VOID 상태가 보존됨

## 2. Method Admission Gate

각 규칙을 `CURRENT_COMMON_CORE, METHOD_SPECIFIC, POST_CHART_SCHOLAR, HISTORICAL_SUPPORT, HOLD` 중 하나로 판정한다.

다음은 방법 결속 없이 실행하지 않는다.

- Bhava/Chalit/Sripathi 계산
- Arudha·Jaimini 계열
- strength·aspect 합성
- Yoga 성립·취소·활성화
- Dasha 종류·시작점·Varga 적용
- Bhinna·SAP·TKS·EKS·Spd
- Pushkara·Upagraha·Mrityu·특수점

통과조건:

`method_id + formula/settings + applicable_scope + required_inputs + exceptions + source_refs`가 닫힘.

## 3. Menu and Dependency Gate

[vedic-submenu-registry.json](vedic-submenu-registry.json)의 semantic module ID를 권위값으로 사용한다.

- 세 수준은 하나의 공통 메뉴를 공유한다.
- 수준을 별도 스킬로 만들지 않는다.
- 여러 adapter의 숫자가 다르면 semantic ID로 변환한다.
- Master 기준 `20=Yoga`, `21=Transit`을 고정한다.
- Varga Mini/Full의 Master 13/14와 legacy coordinate 0-1/0-2를 같은 Job에서 중복 실행하지 않는다.
- Ava 1과 Ava 2를 병합하지 않는다.
- Spd를 Sdp로 자동 치환하지 않는다.

Dependency가 없는 후속 Module은 그 Module만 `HOLD`한다. 독립 Module의 PASS를 지우지 않는다.

## 4. 19-Layer Gate

정확한 Master 순서:

`1 → 2 → 3 → 4 → D-1 → 5-4 → 6 → 7 → 8 → 9 → 10 → 12 → 13 → 14 → 17 → 18 → 19 → 20 → 21`

- `D-1 = 5-1 Pushkara → 5-2 Upagraha → 5-3 Chalit/Sripathi`
- `5-4 Moon`은 독립층
- `7`은 강도·Aspect 비가산 결합층
- `10` Bhinna와 `12` SAP/TKS/EKS/Spd는 독립 단계
- `17` Dasha는 시간창
- `18` Timing Gate는 match
- `19` Ava2는 match 이후 조건
- `20` Yoga는 성립조건
- `21` Transit은 기준시점 맥락

층 존재와 적용을 분리한다. 현재 Target에 미적용이면 `NOT_APPLICABLE`, 필요한 Source·방법이 없으면 `HOLD`다.

## 5. Three-Level Promotion Gate

선택된 각 층은 다음 방향으로만 승급한다.

### ELIVEDIC

`직접값 → locator → 경계 → 미상·충돌 → 다음 입력`

해석·인과·귀속을 만들지 않는다.

### ELICOLLEGE

`관찰 비교 → 패턴후보 → 지지값 → 대조·예외 → 구조해석`

최종 인과·최종 귀속·사건확정을 만들지 않는다.

### ELIPHD

`닫힌 후보 → 층간 관절 → 원인·조건 → 매개·처리 → 판정 → 귀속·회수 → 반사실 한계 → 잔존`

Source와 관절이 닫히지 않은 후보를 최종 주장으로 승격하지 않는다. 뒤 수준이 앞 수준의 Source값을 수정하지 않는다.

## 6. Operator Gate

[analysis-operator-contract.md](analysis-operator-contract.md)의 명시 정의와 필수출력을 사용한다.

항상 실행:

`STRUCTURE → EXTRACT → ASSUMPTIONS → TRACE → FACTCHECK → SYNTHESIZE`

사용자 호출 또는 현재 Target에 필요한 경우만 실행:

`EXPAND, EXPLAIN, IMPLICATIONS, IMPLICITPREMISES, INFER, INNERARCHITECTURE, INTERPRET, INVARIANTS, ITERATE, KEYPOINTS, LAYER, LAYERBOUNDARY, LAYERMAP`

`IN_PROGRESS`는 연산자가 아니라 실행상태다.

## 7. Rule and Case Gate

최종 해석에 사용된 rule마다 다음을 확인한다.

1. exact Source claim이 있는가.
2. 적용 D-chart·House·Module이 맞는가.
3. 계산·방법 설정이 맞는가.
4. 예외·반례·취소조건을 검사했는가.
5. 현재 chart actual value와 match하는가.
6. 동일 Source·동일 case를 중복 증거로 세지 않았는가.
7. 적용되지 않은 규칙이 후속 단계에 재진입하지 않았는가.

worked case는 규칙의 설명·회귀검증 자료다. case 한 건이 규칙의 보편 타당성을 만들지 않는다.

## 8. Synthesis Gate

다음을 별도 배열로 보존한다.

- `confirmed`
- `conditional`
- `conflicts`
- `holds`
- `not_applicable`
- `filtered_claims`
- `final_structure`

최종문은 다음 경로가 역추적돼야 한다.

`Source 직접관찰 → 규칙·방법 입장 → 비교·예외 → 층관절 → ELIPHD 심층구조 → 현재 질문의 직접답`

충돌 평균·빈칸 추정·유창한 가짜 인과를 금지한다.

## 9. Reality and Risk Gate

- 구조층만으로 사건발생·정확한 시기·확률을 확정하지 않는다.
- Dasha·Timing Gate·Ava2·Transit이 있어도 각자의 역할을 넘지 않는다.
- 공동장·Aspect·반복·도수순을 자동 인과·시간순으로 바꾸지 않는다.
- 건강·법률·재정·생사 고위험 결론을 차트만으로 사실 확정하지 않는다.
- 조티시 내부의 방법 합의를 자연과학의 실증적 합의로 표현하지 않는다.

## 10. FNa98 Final QA

각 관문을 독립 판정한다.

1. `TARGET_MATCH`
2. `SOURCE_PROVENANCE`
3. `SOURCE_DEDUPLICATION`
4. `METHOD_BINDING`
5. `MENU_ROUTE`
6. `LAYER_ORDER`
7. `LAYER_BOUNDARY`
8. `THREE_LEVEL_AUTHORITY`
9. `RULE_ADMISSION`
10. `CASE_AND_COUNTEREXAMPLE`
11. `OPERATOR_INTEGRITY`
12. `ASSUMPTION_DISCLOSURE`
13. `TRACE_AND_CAUSAL_JOINTS`
14. `RASHI_BHAVA_NON_DELETION`
15. `STRENGTH_ASPECT_NON_ADDITIVE`
16. `TIMING_ROLE_SEPARATION`
17. `SYNTHESIS_INTEGRITY`
18. `WHY_COMPLETENESS`
19. `FORMAT_AND_DELIVERABLE`
20. `STOP_CONDITION`

판정:

- `PASS`: 현재 요청의 필수 관문 통과
- `REVISE`: Source는 있으나 수정 가능한 결함 존재
- `HOLD`: 필수 Source·방법·권한 부족
- `CONFLICT`: 동등 권위 근거 충돌

`NOT_APPLICABLE` 관문은 실패로 계산하지 않는다.

## 11. 최종 출력

기본 출력은 다음 순서다.

1. 현재 질문의 직접 결론
2. 결정적 Source·규칙·차트관절
3. 왜 그렇게 되는지의 작동경로
4. 성립조건·예외·반례
5. 귀속·회수·잔존 또는 후속 함의
6. 정확한 HOLD·CONFLICT

전체 DB 원장·57 agent packet·QA 표는 사용자가 요청할 때만 펼친다.

## 12. 완료선 분리

- `ARCHITECTURE_PASS`: 본체 메뉴·DB 계약·규칙 승급·라우팅·종결 게이트가 검증됨
- `CORPUS_IN_PROGRESS`: 실제 Source 수집·passage 구조화·RULE_CARD 작성이 진행 중
- `MODULE_PASS`: 지정 Module의 규칙·예외·case가 실행 검증됨
- `CHART_JOB_PASS`: 지정 D×H×Module×Level 결과가 FNa98을 통과함
- `FULL_SYSTEM_PASS`: 요청된 전체 범위의 모든 Module과 corpus가 검증됨

`ARCHITECTURE_PASS`를 `FULL_SYSTEM_PASS`라고 부르지 않는다. 현재 작업에서 실행한 범위만 완료로 판정한다.
