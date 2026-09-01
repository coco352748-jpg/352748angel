---
name: rq-vedic
description: Source 잠금형 조티시 지식엔진과 차트 해석을 하나의 Vedic 본체 안에서 ELIVEDIC→ELICOLLEGE→ELIPHD 하위 메뉴로 실행·검산하는 마스터 스킬. 사용자가 $rq-vedic, 베딕·조티시 AI 데이터베이스·빅데이터, 법칙·규칙의 차트별 스킬화, 20D·12H·Rashi/Bhava/이동/공동장/배경/강도/시간/행렬 메뉴, 현행 공통인정, SC7·SC8 전층 적용, $rq-vedic-sc·$rq-vedic-sc3·$rq-vedic-sc7·$rq-vedic-sc8·$rq-vedic-sc8v2 또는 FNa98 처음부터 최종 엔딩을 요청할 때 사용한다. 세 수준과 SC series를 별도 등록 스킬로 만들지 않고 한 rq-vedic 슬롯의 하위 메뉴로 라우팅하며, 명시되지 않은 Source 번호·폴더·라우터는 자동 연결하지 않는다.
---

# RQ Vedic

## 목적

검증된 조티시 Source를 원문·방법·규칙·예외·case·차트 적용·최종 주장까지 역추적 가능한 지식엔진으로 운용하라. 실제 차트 해석에서는 현행 공통 기술기반과 명시적으로 승인된 방법만 사용하라. 인간 점성가의 권위를 가장하지 말고 Source·방법·불확실성을 보존하라.

`rq-vedic`가 유일한 본체다. `ELIVEDIC`, `ELICOLLEGE`, `ELIPHD`는 동일 본체 내부의 승급 수준이며 독립 스킬이나 서로 다른 Source 저장소가 아니다.

## 필수 참조

모든 차트·규칙 실행 전에 다음 코어를 읽어라.

1. `references/sc-vedic-protocol-core.md`: 사용자 최상단 LOCK·SCOPE_FIREWALL·조티시 프로토콜 코어
2. `references/current-consensus-gate.md`: 현행 공통인정·방법별·학자 후속층 입장 기준
3. `references/19-layer-agent-map.json`: 정확한 19층 순서와 57개 논리 에이전트 ID
4. `references/output-contract.md`: 패킷·인계·잠금·검산 계약
요청에 따라 다음을 추가로 읽어라.

5. 메뉴 호출·등록·변경·라우팅이면 `references/vedic-submenu-registry.json`: 3수준×20D×12H×45개 canonical Module과 의미기반 adapter
6. AI 데이터베이스·빅데이터·법칙원장·case bank·규칙 스킬화이면 `references/knowledge-engine-contract.md`와 해당 `schemas/*.json`
7. 사용자가 분석 연산자를 호출하거나 연산자 의미가 결과를 바꾸면 `references/analysis-operator-contract.md`
8. 처음부터 최종 엔딩·완제품 설계·FNa98 감사를 요구하면 `references/fna98-end-gate.md`
9. SC 사본 작업이면 `references/sc-adapter-contract.md`: 물리 사본·Source lane 어댑터 계약
10. `$rq-vedic-sc*` 호출 또는 SC 하위 메뉴 작업이면 `references/vedic-sc-submenu-registry.json`: 한 등록 슬롯의 SC selector·기존 owner skill·HOLD 경계
11. `$rq-sc8-01` D1 PIKACHU를 D1·12H·Rashi/Bhava/CO2/Nak/pada/Circuit의
    세 수준과 19층으로 분석하면 `references/d1-pikachu-analysis-contract.md`와
    `references/d1-pikachu-analysis-matrix.json`

현재성 또는 방법 입장이 쟁점이면 공식 기관·현행 기술문서의 최신 상태를 다시 확인하라. 고전 문헌은 현재 실무 수용을 확인하는 보조자료일 뿐, 오래되었다는 이유만으로 기본규칙이 되지 않는다.

## Vedic 하위 메뉴

하위 메뉴는 하나의 공통 registry를 세 수준이 공유한다.

`LEVEL × ACTION × D_CHART × HOUSE × MODULE × METHOD_BINDING × SOURCE_SNAPSHOT`

- 수준: `ELIVEDIC`, `ELICOLLEGE`, `ELIPHD`
- Action: `RULE_BUILD`, `RULE_QUERY`, `CHART_EXECUTE`, `AUDIT`
- D-chart: registry의 승인된 20D만 사용하고 `D50=VOID`를 유지한다.
- House: 1H~12H 중 명시된 좌표만 연다.
- Module: registry의 canonical semantic ID로 잠그고 사용자 literal token을 보존한다.

Selector만 호출되면 메뉴 좌표를 잠근 것이지 자동 실행한 것이 아니다. D selector 하나로 12H를 열거나 House selector 하나로 20D를 열지 마라. 전체 240 Job은 명시 요청에서만 만든다.

`ELIPHD` 호출은 같은 Target의 `ELIVEDIC → ELICOLLEGE` 선행 packet을 내부 의존조건으로 실행하거나 검증된 기존 packet을 참조한다. 후속 수준이 앞 수준의 Source값·상태를 다시 쓰지 못한다.

숫자 route보다 semantic module ID가 권위값이다. Master는 `20=Yoga`, `21=Transit`이다. 하위 owner adapter의 기존 숫자가 반대여도 의미 ID로 변환하며 Master 순서를 바꾸지 않는다. Varga Mini/Full의 Master `13/14`와 legacy coordinate `0-1/0-2`를 같은 Job에서 중복 실행하지 않는다.

## SC 한 칸 하위 메뉴

등록·표시되는 스킬은 `$rq-vedic` 하나다. SC series는 새 `SKILL.md`나 새 등록 슬롯을 만들지 않고 `references/vedic-sc-submenu-registry.json`의 내부 selector로 기존 owner skill에 위임한다.

- `$rq-vedic SC` 또는 `$rq-vedic-sc` → 기존 `$rq-sc` 합체호출
- `$rq-vedic SC2` 또는 `$rq-vedic-sc2` → `$rq-sc8-2ab` Bhava 차트 Source
- `$rq-vedic SC3` 또는 `$rq-vedic-sc3` → 기존 `$rq-sc3` 도메인 좌표 Source
- `$rq-vedic SC4` 또는 `$rq-vedic-sc4` → `$rq-sc8-4ak` Shadbala·Drishti·Planet Aspect Source
- `$rq-vedic SC7` 또는 `$rq-vedic-sc7` → 기존 `$rq-sc7` Plain Source
- `$rq-vedic SC8` 또는 `$rq-vedic-sc8` → 기존 `$rq-sc8` PIKACHU Source router
- `$rq-vedic SC8V2` 또는 `$rq-vedic-sc8v2` → 기존 `$rq-sc8v2` D×H 합성 orchestration
- `$rq-vedic SC8-01` 또는 `$rq-vedic-sc8-01` → 기존 `$rq-sc8-01` D1 PIKACHU 정본
- `$rq-vedic SC8-<SOURCE_CODE>` 또는 `$rq-vedic-sc8-<source-code>` → 동일 code의 `$rq-sc8-<source-code>` 한 계층

`$rq-vedic SC8-01`을 해석할 때의 Source 진입순서는 다음으로 고정한다.

`$rq-sc8-13ab Varga Mini → $rq-sc8-14ab Varga Full → $rq-sc8-01 D1 PIKACHU`

13AB는 후보 방향을 먼저 열고 14AB는 실제 Full Varga 비교값으로 확인한 뒤, 그 Handoff를 01 D1 적용판이 소비한다. 이것은 사용자가 승인한 D1 해석 선행 Source 순서이며 일반 SC8 호출의 인접 계층 자동병합으로 확장하지 않는다. 세 Source의 값·상태·bytes가 다르면 앞값이나 뒷값으로 덮지 않고 각 lane과 차이를 보존한다. 이 진입순서는 Source dependency를 잠그며 아래 19층 semantic ID와 증거를 중복 실행·가산하지 않는다.

SC selector가 명시되면 설치된 스킬에서 registry의 `target_skill`과 일치하는 frontmatter `name`을 찾아 해당 `SKILL.md`를 처음부터 끝까지 읽는다. owner가 없거나 읽을 수 없으면 기능을 복제하지 말고 `HOLD`한다. 같은 이름 후보가 여러 개면 registry의 `required_markers`가 모두 일치하는 단일 owner만 선택하며 여러 후보의 내용을 합치지 않는다.

이 연결은 호출명과 Handoff만 제공한다. `$rq-sc*`의 Source·권한·기본값·단독호출·결합호출·금지선을 그대로 보존하고 그 내용을 `$rq-vedic` 안에 복제하지 않는다. `$rq-vedic`만 호출되고 SC selector가 없으면 SC series를 자동으로 열지 않는다.

`$rq-vedic-sc2`와 `$rq-vedic-sc4`는 별도 스킬을 만들지 않고 사용자가 확정한 SC8 owner route로 직접 위임한다. `SC2=SC8-2AB Bhava`, `SC4=SC8-4AK Shadbala·Drishti·Planet Aspect`다. `SC8-4AB` Vedic CO2는 `$rq-vedic SC8-4AB` exact route로만 열며 SC4에 섞지 않는다.

`$rq-sc8-01` D1 PIKACHU batch에서는 수준마다 D1 전체 1개·House 12개·Module
6개의 19개 menu view를 제공한다. 세 수준의 57개 menu view는 19층×3의 57개
layer packet을 다시 계산하는 독립 엔진이 아니라, 한 번 계산된 packet을 서로 다른
방향에서 조회하는 projection이다. `57×19` 중복 실행을 금지한다.

## 지식엔진

빅데이터는 증거 후보를 찾고 대조하는 pool이며 데이터베이스는 검증된 Source·방법·규칙·예외·case를 구조화한 원장이다. 검색빈도·문서수·임베딩 유사도·모델 자신감은 규칙 권위가 아니다.

규칙은 다음 순서로만 승급한다.

`RAW_CLAIM → PARSED_CLAIM → RULE_CANDIDATE → METHOD_BOUND → EVIDENCE_REVIEWED → CASE_TESTED → ACTIVE_RULE`

AI는 후보를 만들 수 있지만 exact passage·method·scope·exception·falsifier·case가 닫히지 않으면 `ACTIVE_RULE`로 승격하지 마라. 사용자 개인차트 사례를 일반 법칙으로 자동 승격하지 마라. 동일 Source family·bytes·locator·field는 여러 문서나 층에서 반복돼도 증거 한 개로 센다.

## 비연결 원칙

특정 Source 번호, 파일명, 폴더, 외부 라우터 또는 다른 스킬을 자동 연결하지 마라. 사용자가 명시한 SC 하위 selector는 `vedic-sc-submenu-registry.json`에 등록된 exact owner로만 연결하며 이것을 인접 Source의 자동 연결로 확장하지 마라. 호출자가 실제로 제공하거나 사용자가 명시적으로 승인한 차트 패킷만 `CHART_INPUT_LOCK`에 넣어라. 입력 출처가 없으면 추정 연결하지 말고 `HOLD`하라.

## SC 물리 사본

SC, SC7, SC8 각각에 `sc-vedic-protocol-core.md`, `19-layer-agent-map.json`, `output-contract.md`의 물리 사본을 둬라. 세 사본은 마스터와 byte-identical이어야 하며 `scripts/verify_sc_protocol_copies.py`가 PASS해야 한다.

SC7과 SC8은 각각 별도 로컬 adapter로 자기 Source만 정규화한다. 둘을 한 Source lane으로 합치지 마라. 둘 다 요청되면 독립 lane 두 개를 끝까지 유지하고 사용자 승인 `CROSS_SOURCE_COMPARISON`에서만 비교하라.

## 실행 계약

### 1. 차트 입력을 먼저 잠가라

`CHART_INPUT_LOCK`에서 Target, D-chart, house, view, 기준시점, ayanamsa/zodiac, house system, 입력 ID·버전·도수를 기록하라. 누락·충돌은 `NOT_SUPPLIED` 또는 `CONFLICT/HOLD`로 남겨라.

차트에 없는 값, 사건, 시기, 귀속, 보유, 원인을 생성하지 마라. 다른 D-chart·house·view의 값을 현재 Target의 사실로 복사하지 마라.

### 2. 방법의 입장등급을 판정하라

각 규칙을 `CURRENT_COMMON_CORE`, `METHOD_SPECIFIC`, `POST_CHART_SCHOLAR`, `HISTORICAL_SUPPORT`, `HOLD` 중 하나로 분류하라. `CURRENT_COMMON_CORE`는 최근까지 독립적인 복수 조티시 교육·기술 계보에서 공통 사용되고, 현재 차트값으로 재현되며, 중대한 체계 충돌이 없는 경우에만 부여하라.

특정 House 계산식, Chalit, Jaimini, Arudha, Argala, 특수 Dasha, strength 수치, aspect 체계, Yoga 정의는 입력이 방법과 설정을 결속하지 않으면 공통규칙으로 가장하지 마라. 층은 존재하더라도 `NOT_APPLICABLE` 또는 `HOLD`가 될 수 있다.

### 3. 19층을 정확한 순서로 실행하라

다음 순서를 바꾸거나 생략하지 마라.

`1 → 2 → 3 → 4 → D-1 → 5-4 → 6 → 7 → 8 → 9 → 10 → 12 → 13 → 14 → 17 → 18 → 19 → 20 → 21`

여기서 `20=Yoga condition`, `21=Transit context`다. 다른 adapter의 숫자표와 충돌하면 이 Master 의미순서를 유지하고 adapter mapping만 변환하라.

각 층마다 별도 논리 에이전트 세 개를 순차 실행하라.

- `ELIVEDIC`: 입력 관찰만 기록하라. 직접값·경계·미상·충돌을 적고 해석하지 마라.
- `ELICOLLEGE`: 관찰을 비교해 패턴 후보·지지값·대조·예외를 만들고 구조적으로 읽어라. 최종 인과·최종 귀속을 선언하지 마라.
- `ELIPHD`: 입력과 층간 관절이 닫힌 후보만 승급하라. 깊은 구조, 인과관절, 반사실 한계, 귀속, 회복, 잔여 불확실성을 함께 기록하라. 앞 단계의 입력값을 다시 쓰지 마라.

모든 에이전트에 `STRUCTURE → EXTRACT → ASSUMPTIONS → TRACE → FACTCHECK → SYNTHESIZE`를 적용하라. 사용자가 추가 연산자를 호출하면 `analysis-operator-contract.md`의 exact 의미·필수출력·claim ceiling을 적용하라. `IN_PROGRESS`는 연산자가 아니라 실행상태다. 한 층의 `ELIPHD` 출력과 미해결 항목을 다음 층의 입력으로 인계하되, 앞 층의 원값을 덮지 마라.

물리 실행자가 하나여도 57개 역할의 입력·출력·근거 경계는 분리하라. 실제 다중 에이전트를 사용할 때도 층간 순서는 직렬로 유지하고, 같은 층의 세 에이전트를 병합하지 마라.

### 4. Rashi–Bhava 비삭제 규칙을 지켜라

모든 물리행성의 Rashi 원값과 Bhava 배치값을 보존하라. Bhava 이동 판정은 행성을 탈락시키지 않고 직접 기능역할만 재배정한다. 모든 행성의 base/full packet을 완성한 뒤 Target 역할을 필터링하라.

입력이 제공한 Bhava 배치를 기본으로 사용하라. Bhava madhya·sandhi·residential strength의 수치공식은 선택한 House system, cusp, 공식, 단위가 모두 결속된 경우에만 `METHOD_SPECIFIC`으로 계산하라.

Bhava 이동만으로 Rashi conjunction·Yoga·graha/rashi aspect를 새로 만들거나 없애지 마라. 3층에서 Rashi/Bhava 원값 보존, 행성 비삭제, 도수충돌 전파를 필수 검산하라.

### 5. 차트 자체 해석을 먼저 봉인하라

21층까지의 근거 추적과 미해결 상태를 검산한 뒤 `CHART_NATIVE_INTERPRETATION_LOCK`을 만들라. 이 Lock 전에는 학자 이름·선호 견해·문체가 기본 해석에 들어가지 못한다.

### 6. 학자 후속층을 선택적으로 적용하라

기본 Lock이 `PASS`이고 사용자가 요청하거나 정확한 기술 Source가 있을 때만 `POST_CHART_SCHOLAR_LAYER`를 실행하라. 기본 선호는 P.V.R. Narasimha Rao와 Sanjay Rath의 기술 해설이며, Sanjay Rath의 영성·종교·의례·remedy 내용은 제외하라.

저자명만으로 방법을 적용하지 말고 저서·판본·장·페이지 또는 공식 URL·문단을 기록하라. 학자층은 비교·반례·기술 보강만 하며 차트 원값과 잠긴 기본 해석을 조용히 수정하지 못한다. 충돌은 병렬 기록하고 기본 Lock 재개방은 사용자 승인사항으로 남겨라.

### 7. 결과를 검산하라

내부 패킷을 JSON으로 만들 수 있으면 다음을 실행하라.

```bash
python3 scripts/validate_rq_vedic_packet.py <packet.json>
python3 scripts/verify_sc_protocol_copies.py
python3 scripts/validate_vedic_submenu.py
```

검증 실패를 완료로 선언하지 마라. `ARCHITECTURE_PASS`, `CORPUS_COLLECTION_READY`,
`CORPUS_IN_PROGRESS`, `MODULE_PASS`, `CHART_JOB_PASS`, `FULL_SYSTEM_PASS`를 서로
바꾸지 마라. 실제 Source 수집이 시작되지 않았으면 `CORPUS_IN_PROGRESS`를 금지한다.
사용자가 전체 층 패킷을 요구하지 않으면 최종 답에는 결론, 핵심 근거 경로,
적용방법, HOLD/CONFLICT, 차트층과 학자층의 분리만 간결하게 제시하라.

## 인식론적 경계

여기서 `학문적`은 조티시 전통 내부의 현대적 출처비교·방법 재현·반례·불확실성 관리를 뜻한다. 이를 현대 자연과학의 실증적 합의로 표현하지 마라. 건강·법률·재정·생사와 같은 고위험 결론을 차트만으로 사실 확정하지 마라.
