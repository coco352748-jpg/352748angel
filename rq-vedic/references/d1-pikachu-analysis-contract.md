# D1 PIKACHU 3수준·19층 분석 계약

`CONTRACT_ID=RQ_VEDIC_D1_PIKACHU_ANALYSIS_V1`

## 1. 목적과 경계

이 계약은 기존 `rq-vedic` 본체 안에서 `$rq-sc8-01`이 공급하는 D1 PIKACHU
정본을 다음 세 수준으로 분석하기 위한 D1 전용 하위 메뉴다.

`ELIVEDIC → ELICOLLEGE → ELIPHD`

새 스킬을 만들지 않는다. 세 수준은 같은 Source snapshot·같은 19층·같은 분석셀을
공유한다. 뒤 수준은 앞 수준의 직접값을 고치거나 새 Source로 바꾸지 못한다.

현재 요청의 기본 Module 범위는 다음 여섯 개다.

`RASHI, BHAVA, CO2, NAK, pada, Circuit`

`CO2=CO_PRESENCE_FIELD`다. 이동판정과 동일시하지 않는다. 사용자가 19층을 함께
요청했으므로 이동판정은 19층의 3층에서만 별도 실행한다. 배경·강도·시간층도
19층 안에서만 열며 여섯 Module 메뉴에 조용히 합치지 않는다.

## 2. Source 호출

### 2.1 해석 선행 Varga route

D1 PIKACHU 해석을 실행할 때는 다음 Source 진입순서를 먼저 잠근다.

```text
PRE_INTERPRETATION_SOURCE_ORDER=$rq-sc8-13ab → $rq-sc8-14ab → $rq-sc8-01
STEP_1=Varga Mini candidate
STEP_2=Varga Full confirmation
STEP_3=D1 PIKACHU applied target
HANDOFF_LOCK=VARGA_MINI_TO_VARGA_FULL_TO_D1_PIKACHU
```

- `$rq-sc8-13ab`: `07_13AB_MiNi_Varga.zip`의 `07_13AB_D1_MiNi_Varga.txt`
- `$rq-sc8-14ab`: `07_14AB_F_Varga.zip`의 `07_14AB_D1_F_Varga.txt`
- `$rq-sc8-01`: 두 선행 Varga lane을 참조한 뒤 D1 PIKACHU 적용판을 연다.

13AB·14AB·01의 Varga member는 byte-identical이라고 가정하지 않는다. 서로 다른 값·상태·
변환문이 있으면 Source lane별로 보존하고 `DIFFERENCE/CONFLICT`를 전파한다. 선행 Source의
존재를 01 안의 13·14층에 새 증거로 다시 가산하지 않는다.

이것은 D1 해석의 Source dependency 순서다. 19개 semantic layer의 ID를 바꾸거나
13·14를 두 번 실행하는 규칙이 아니다.

### 2.2 D1 정본 route

```text
CALL=$rq-sc8-01
TARGET=D1 PIKACHU
PACKAGE=assets/pikachu-sc-canonical/01_AB_D1_PicAcHu_☆.zip
SOURCE_PROVIDER=rq-sc8
SOURCE_MODE=EXPLICIT_CANONICAL_DCHART_ROUTE
```

`$rq-sc8-01`은 `$rq-sc8-1ab`의 별칭이 아니다.

- `$rq-sc8-01`: D1 PIKACHU flat package 전체를 고정하는 D-chart route
- `$rq-sc8-1ab`: 번호 1 Rashi Source family만 공급하는 layer route

두 호출은 Source 범위와 결과가 다르다. 같은 것으로 병합하지 않는다.

### 2.3 여섯 Module의 직접 Source

- `RASHI`: `02_1A_D1_RaShi_12H_AppLieD_R.txt`
- `BHAVA`: `02_1B_D1_Bha_12H_AppLieD_R.txt`
- `CO2`: `04_1A_D1_CoPreSeNcE_12H_AppLieD_R.txt`
- `NAK`: 위 세 parent member 안의 Nakshatra 직접필드만 lane별 투영
- `pada`: 위 세 parent member 안의 Pada 직접필드만 lane별 투영
- `Circuit`: 위 세 parent member 안의 RL/NL/SL/SSL 직접필드만 lane별 투영

NAK·pada·Circuit은 독립 원본이 아니다. 다음 세 projection lane을 유지한다.

```text
RASHI_PROJECTION
BHAVA_PROJECTION
CO2_PROJECTION
```

세 lane의 값이 같아도 증거를 세 개로 부풀리지 않는다. 값이 다르면 평균·교체하지
않고 `DIFFERENCE` 또는 `CONFLICT`로 남긴다.

## 3. 분석 데이터 큐브

직접 분석 단위는 다음 하나뿐이다.

`D1 × 12H × 6 MODULES × 3 LEVELS = 216 CORE CELLS`

각 셀은 다음을 가진다.

```text
cell_id
source_lane
source_member
source_locator
direct_fields
method_admission
level
claims
unknowns
conflicts
handoff_ref
```

216개 셀을 먼저 만들고 메뉴가 이를 서로 다른 방향에서 조회한다. 메뉴마다 Source를
다시 추출하거나 같은 해석을 재생산하지 않는다.

## 4. 사용자 메뉴 57개

수준마다 정확히 19개 view를 둔다.

1. `D1` view 1개: 12H×6 Module의 차트 전체 투영
2. `1H~12H` view 12개: 해당 House×6 Module의 하우스 투영
3. `RASHI/BHAVA/CO2/NAK/pada/Circuit` view 6개: 해당 Module×12H의 모듈 투영

따라서 다음이 성립한다.

```text
19 VIEWS PER LEVEL × 3 LEVELS = 57 MENU VIEWS
```

`ELI VEDIC`은 `ELIVEDIC`의 literal alias다. 두 표기를 별도 수준으로 세지 않는다.

### 4.1 D1 view

- `ELIVEDIC D1`: 전체 직접값·빈칸·경계·충돌 지도
- `ELICOLLEGE D1`: 12H와 여섯 Module 사이의 패턴후보·대조·예외·구조해석
- `ELIPHD D1`: 19층에서 닫힌 관절만 사용한 D1 최종 구조·한계·잔존

### 4.2 House view

- `ELI VEDIC <n>H`: 한 House의 여섯 Module 직접 관찰
- `ELICOLLEGE <n>H`: 같은 House 안의 지지·압박·연결·예외 후보
- `ELIPHD <n>H`: 19층에서 확인된 해당 House의 내부 배치·전달·귀속·잔존

### 4.3 Module view

- `ELI VEDIC <MODULE>`: Module의 12H 직접값과 Source 경계
- `ELICOLLEGE <MODULE>`: 12H 비교·패턴후보·대조·예외
- `ELIPHD <MODULE>`: 확인된 층간 관절과 반사실 한계를 포함한 Module 최종 구조

현재 요청처럼 `$rq-sc8-01`과 `분석`이 함께 잠긴 batch 안에서는 위 selector를
`CHART_EXECUTE` view로 실행한다. batch 밖에서 selector만 단독 호출되면 기존
registry 규칙대로 navigation이며 자동 실행하지 않는다.

## 5. 세 수준의 승급

### ELIVEDIC

직접값·locator·경계·미상·충돌만 기록한다. Rashi sign, occupants, lord position,
degree, Nakshatra, Pada, RL/NL/SL/SSL, 공동장 존재와 같은 확인값을 해석문으로
바꾸지 않는다.

### ELICOLLEGE

같은 셀의 ELIVEDIC packet을 입력으로 받는다. House·Module·축·lord route를
비교하고 패턴후보·지지값·대조·예외·구조적 의미를 설명한다. 최종 인과·사건발생·
최종귀속은 선언하지 않는다.

### ELIPHD

ELIVEDIC와 ELICOLLEGE가 모두 PASS하고 rule·method·예외가 닫힌 주장만 승급한다.
깊은 구조·인과관절·반사실 한계·귀속·회수·잔여 불확실성을 함께 기록한다.
여기서 인과는 조티시 해석모형 내부의 구조관절이며 현실세계의 과학적 원인 확정이 아니다.

규칙 corpus가 없는 경우 ELIVEDIC 직접관찰은 실행할 수 있지만 ELICOLLEGE와
ELIPHD의 해당 rule-dependent claim은 `HOLD`다. 문장 깊이로 규칙 공백을 채우지 않는다.

## 6. 19층 본체 엔진

선행 Varga route에서 만든 `VARGA_MINI_TO_VARGA_FULL_TO_D1_PIKACHU` Handoff를
입력 dependency로 잠근 뒤 다음 19층을 각각 한 번만 순차 실행한다.

`1 → 2 → 3 → 4 → D-1 → 5-4 → 6 → 7 → 8 → 9 → 10 → 12 → 13 → 14 → 17 → 18 → 19 → 20 → 21`

각 층에 `ELIVEDIC → ELICOLLEGE → ELIPHD`를 적용하므로 내부 layer packet은
`19×3=57`개다. 이것은 사용자 메뉴 57개와 다른 축이다.

- layer packet: 근거가 처리되는 순서
- menu view: 처리된 결과를 D1·House·Module 방향에서 보는 창

`57 MENU VIEWS × 19 LAYERS`의 Cartesian 복제를 금지한다. 각 menu view는 필요한
layer output ref만 조회한다.

### 6.1 층과 Source member

- `1 Rashi`: `02_1A_D1_RaShi_12H_AppLieD_R.txt`
- `2 Bhava`: `02_1B_D1_Bha_12H_AppLieD_R.txt`
- `3 Rashi-Bhava move`: `HYEWON_D1_RASHI_BHAVA_03_FIRST_INTEGRATION_PROMISE_LINKED_APPLIED_98.txt`
- `4 Co-presence`: `04_1A_D1_CoPreSeNcE_12H_AppLieD_R.txt`
- `D-1`: Pushkara·Upagraha·Spirit Chalit 세 member
- `5-4`: Moon member
- `6`: Arudha member
- `7`: Shadbala A/R·Bhava Bala·Vimsopaka·Planet/Aspect02/Aspect03 member
- `8`: Mrityu·SPother member
- `9`: Ava1 member
- `10`: Bhinna Matrix member
- `12`: SaP·Tks·Eks·SpD 네 member
- `13`: Varga Mini member
- `14`: Varga Full member
- `17`: Dasha member
- `18`: Timing Gate member
- `19`: `$rq-sc8-19ab`의 D1 Ava2 member
- `20`: `$rq-sc8-20ab` Yoga Source의 D1 범위
- `21`: `$rq-sc8-21ab` Transit Source와 명시 기준시점

`3P_1AB_o0o0o_D1_AppL.txt`는 결합·확장본이므로 기본 증거로 다시 세지 않는다.
원자 member 검산용 derived container로만 둔다.

### 6.2 시간층 경계

정적 D1 구조질문에서 17·18·19·21은 자동으로 시기결론을 만들지 않는다.
시간 질문·Dasha method·기준시점이 없으면 `NOT_APPLICABLE` 또는 `HOLD`다.
Transit snapshot의 날짜를 현재시점으로 바꾸지 않는다.

현재 `$rq-sc8-21ab` Transit member의 natal D1 참조에는 Rahu·Ketu 24:58:08과
SL Ra가 있고, `$rq-sc8-01` D1 package에는 26:33:09와 SL Ju가 있다. 이것은
서로 다른 Source lane의 `KNOWN_CROSS_LANE_DIFFERENCE`다. Transit member의 natal
참조값은 `TRANSIT_SCREEN_CONTEXT_ONLY`이며 `$rq-sc8-01` 값을 덮어쓰지 못한다.
반대로 차이를 삭제하거나 평균내지도 않는다. Node 값에 의존하는 시간주장은 사용자
승인 권위값이 잠길 때까지 `HOLD`한다. 이 차이는 정적 D1 구조 view를 자동 무효화하지
않고 21층과 그 값을 참조하는 시간주장에만 전파한다.

## 7. Rashi–Bhava와 공동장 잠금

3층에서 다음이 모두 true여야 한다.

```text
RASHI_RAW_PRESERVED=true
BHAVA_RAW_PRESERVED=true
PLANET_NOT_DELETED=true
DEGREE_CONFLICT_PROPAGATED=true
FULL_PACKET_BEFORE_ROLE_FILTER=true
```

Bhava 이동으로 Rashi conjunction·Yoga·aspect를 생성·삭제하지 않는다. CO2의
행성 도수순은 관찰순서이며 Source·method가 없으면 사건 시간순이나 원인순으로
승격하지 않는다.

## 8. View별 출력계약

각 view는 다음 순서로 출력한다.

1. 현재 view의 직접 결론 또는 직접 관찰
2. 결정적 Source member·House·Module·layer ref
3. 근거에서 판정까지의 작동경로
4. 성립조건·예외·대조·반사실 한계
5. `PASS/REVISE/HOLD/CONFLICT/NOT_APPLICABLE`
6. 다음 수준 또는 최종 synthesis로 넘기는 handoff ref

D1 전체 view는 12개 House 결과를 평균하거나 한 문장으로 압축하지 않는다.
House view는 다른 House의 값을 현재 House의 직접값으로 복사하지 않는다.
Module view는 다른 Module의 권한으로 빈칸을 보충하지 않는다.

## 9. 완료조건

설계 PASS와 차트분석 PASS를 분리한다.

### DESIGN_PASS

- `$rq-sc8-01`이 D1 PIKACHU package에 exact binding됨
- 3수준·12H·6 Module이 고정됨
- 216 core cell과 57 menu view가 결정론적으로 생성됨
- 19층×3=57 layer packet 순서와 Source binding이 검증됨
- no-auto-merge·비삭제·충돌전파·claim ceiling이 잠김

### CHART_JOB_PASS

- 실제 216 cell이 Source locator와 함께 생성됨
- 필요한 rule corpus와 method binding이 존재함
- 19층의 현재 Target 상태가 모두 기록됨
- 필수 HOLD·CONFLICT가 최종 주장으로 승격되지 않음
- 요청된 menu view가 FNa98 QA를 통과함

설계만 끝난 상태를 D1 분석 완료라고 부르지 않는다.
