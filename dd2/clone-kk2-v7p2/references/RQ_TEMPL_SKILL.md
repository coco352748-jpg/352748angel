---
name: rq-templ
description: "RQ VeDic의 Source 잠금형 차트 템플릿 제작·수정·배치·검산 스킬. $rq-templ 또는 legacy $rq-vedic-chart-template-qa로 호출한다. 현재 Target 하나와 완제품 하나를 잠근 뒤 Source Scope→File Family→Stage Role→Input Source→Source Separation→ONE_D×ONE_H 독립 Job→Application Route→Raw Check→Link Check→3PASS→FNa98 Final Output 수명주기를 재사용한다. PIKACHU×SC 정본 경로, Source Router 16 기반 동적 구조관절 경로, 고정 01~20 칼끝문장 경로, 240H 공용 경로를 서로 섞지 않고 실행·검산한다. 실제 차트 Source는 Plain 공급자 $rq-sc7에서 받고, 일반 해석·문장 실현은 $rq-wri에 인계한다."
---

# RQ VeDic 차트 템플릿·구조관절·문장결 검산

## 목적

네 실행 경로를 하나의 Source 입장 게이트 아래에서 서로 섞지 않고 재현한다.

- `PIKACHU_CANONICAL_PATH`: 최신 PIKACHU×SC 정본의 `00A~00C + 01~20 + 병목후 11관절`을 실행골격으로 보존한다. 매 작업에서 `SOURCE_PACKET`, `PREMAP_EXECUTION`, `MASTER_EXECUTION_01_20`, `STAGE_COMMAND_LOCK`, `POST_BOTTLENECK_EXECUTION_01_11`을 새로 만들고 그 패킷에서만 템플릿·분석·해석·문장결·파일을 생산한다.
- `STRUCTURAL_JOINT_DISCOVERY`: `DEEP_DENSE_KNIFE_SENTENCE_TEMPLATE_SET_V2`의 Source Router 16→Evidence Registry→20D 세로축×Target D 12H 가로축→관절은행→동적 01~20 배정→사람말→절별 역매핑을 별도 패킷·별도 검증기로 실행한다. 이 패킷에서 PIKACHU, 00A~00C, PIKACHU MASTER 고정 01~20, 병목후 11관절은 `NOT_USED`다.
- `FIXED_KNIFE_SENTENCE_01_20_PATH`: 사용자가 지정한 고정 《01》~《20》 제목·순서·기능을 유지하고 Google Drive Active Canonical의 Target별 실제값만 넣어 사람말·절별 역매핑·전용 출력검산을 실행한다. 동적 제목 생성과 20 PRIMARY 관절 배정은 이 경로에 적용하지 않는다.
- `DEEP_DENSE_240H_COMMON_PATH`: 20D×H01~H12의 정확히 240개 Job에 공용 심층촘촘결 잠금 구조를 적용한다. 템플의 00A~00C 인계 표기와 01~20·하위단계 순서는 보존하되 `PIKACHU_DEPENDENCY=NOT_USED`로 잠그고, PIKACHU 정본 경로와 `STRUCTURAL_JOINT_DISCOVERY` 패킷 모두에서 분리한다.

`DEEP_DENSE_KNIFE_SENTENCE_TEMPLATE_SET_V2 / V2_REPAIRED`는 현재 사용자의 명시 승인으로 `RQ_VEDIC_SYSTEM_WIDE_FOR_STRUCTURAL_JOINT_DISCOVERY` 범위의 `ACTIVE_CANONICAL`이다. 이 승격은 V2 본문과 동적 실행순서를 전역 선택 대상으로 잠그며, PIKACHU·고정 01~20·240H 공용 경로의 자체 정본을 대체하지 않는다. 정본 교체·해제·재활성화 권한은 사용자에게만 있다.

공통 Source 입장식은 `SC_VERIFIED OR provider-native created_at >= 2026-08-09T00:00:00+09:00`이다. 입장을 통과한 Source만 각 경로의 권한·상태·Target 적합성 검문으로 넘긴다.

## 최상위 Scope Firewall

매 실행에서 가장 최근 사용자 지시 하나만 `CURRENT_TARGET`으로 활성화하고, 사용자가 받아야 할 완제품 하나만 `DELIVERABLE`로 잠근다.

- `IN_SCOPE = 사용자 명시사항 + 완제품 성립에 필수인 직접 의존조건`
- 어떤 읽기·검색·수정·검산도 현재 요구조건과의 `AUTHORIZATION_LINK`가 없으면 실행하지 않는다.
- 이전 미해결작업, 다른 계보, 보유기능, 유지보수, 전체정리, 추가개선을 자동 반입하지 않는다.
- 새 범위가 완제품에 필수이면 실행 전에 사용자 승인을 받고, 필수가 아니면 제외한다.
- 초안·중간본·수정본·진행보고는 사용자에게 내지 않고 내부 `VOID`로 처리한다.
- 설계·판단은 필요한 만큼만 쓰고 실제 완제품 생성에 작업의 60% 이상을 배정한다. 마지막 Target 검산은 10% 이내에서 닫는다.
- `요청 산출물 존재 + 명시조건 충족 + 마지막 검산 완료`가 되면 즉시 종료하며 인접 작업을 이어 붙이지 않는다.

## 필수 참조

0. 모든 작업에서 `references/canonical-registry.md`를 먼저 읽어 현재 경로별 정본과 VOID 경계를 잠근다. `STRUCTURAL_JOINT_DISCOVERY`는 레지스트리의 V2 `ACTIVE_CANONICAL`을 사용하며 다른 경로 정본을 흡수하지 않는다.
1. 모든 작업에서 가장 먼저 `references/source-admission-gate.md`와 `references/authority-and-states.md`를 전부 읽는다. 실제 정본·명령·본체·Support·예시·교차검산 Source에 공통 입장 게이트를 적용하고, 각 패킷 검증기는 `scripts/source_admission.py`를 우회하지 않는다.
2. `STRUCTURAL_JOINT_DISCOVERY`에서는 `references/deep-dense-knife-sentence-template-v2.txt`와 `references/structural-joint-discovery-contract.md`를 전부 읽고 V2의 정확한 Source Router 16·실행순서·동적 01~20·역매핑 계약을 실행골격으로 쓴다. 패킷 작성 후 `python3 scripts/validate_structural_joint_packet.py <packet.json>`을, 최종 사람말 출력 후 `python3 scripts/validate_knife_sentence_v2_output.py <artifact>`를 실행한다.
3. `FIXED_KNIFE_SENTENCE_01_20_PATH`에서는 `references/fixed-knife-sentence-template-01-20.txt`와 `references/fixed-knife-sentence-contract.md`를 전부 읽는다. 고정 제목·순서·기능을 바꾸지 않고 `python3 scripts/validate_fixed_knife_sentence_packet.py <packet.json>`과 `python3 scripts/validate_fixed_knife_sentence_output.py <artifact>`를 모두 실행한다. 실제 차트값에 `$rq-sc7`을 사용하면 현재 `rq-sc7`의 Source 권한 계약을 함께 적용하되 Drive Active Canonical 자동승격으로 바꾸지 않는다. 《05》·《06》의 나크파다·도수·RL/NL/SL/SSL 회로가 현재 질문의 주 Target일 때만 `$rq-nak`을 별도 하위패킷으로 호출하고, 보조 착색층이면 호출을 강제하지 않는다.
4. 사용자 정의 명령 또는 프로젝트 명령이 보이면 `references/command-discovery.md`와 `references/stage-command-matrix.md`를 전부 읽고 원문 정의를 찾은 뒤 단계별 필수 조합을 잠근다.
5. `PIKACHU_CANONICAL_PATH`의 차트 템플릿·분석·해석 작업에서만 `references/pikachu-sc-master-canonical.md`와 `references/micro-house-execution-template.md`를 전부 읽고 00A~00C와 01~20을 수직 완주한다.
6. `PIKACHU_CANONICAL_PATH`에서 도파민결·심층작동결·심층촘촘결이면 `references/three-grain-writing-contract.md`를 전부 읽고, 심층촘촘결·목관절층 해석문·긴 잠금문이면 `references/deep-dense-writing-contract.md`도 전부 읽는다.
7. `DEEP_DENSE_240H_COMMON_PATH`에서는 `references/deep-dense-lock-template-240h.md`를 전부 읽고 정확한 01~20과 각 substage의 문구·순서·소속을 변경·병합·생략하지 않는다. 템플 단계의 Source값 내용검산은 `NOT_APPLICABLE`이고, `python3 scripts/validate_deep_dense_240h_template.py <artifact>`로 제목 토폴로지만 검산한다. 실제 값을 주입하는 240 Job은 각 D×House의 값·문장·HOLD를 독립 처리하고 `$rq-vedic-sentence-twin`을 함께 사용한다. 고정된 00A~00C 인계 표기는 보존하되 PIKACHU 이름·정본·실행골격 의존은 `NOT_USED`다.
8. `PIKACHU_CANONICAL_PATH`의 제작·분석·해석 작업에서 `references/execution-workflow.md`를 전부 읽는다.
9. `PIKACHU_CANONICAL_PATH`에서 병목·뒤집기·회수·최종 마무리가 포함되면 `references/post-bottleneck-recovery-canonical.md`를 전부 읽고 적힌 11관절 순서를 바꾸지 않는다.
10. 모든 경로의 검산·PASS 판정·최종 납품에서 `references/quality-gates.md`를 전부 읽되, 각 경로에서 `NOT_APPLICABLE`로 명시한 게이트를 억지로 실행하지 않는다.
11. `PIKACHU_CANONICAL_PATH` 작업패킷을 만들거나 PASS를 선언하기 전에 `python3 scripts/validate_work_packet.py <packet.json>`을 실행한다. 이 검증기를 다른 세 독립 경로에 사용하지 않는다.
12. RQ18 전층 봉합축·RQ10 병목 뒤집기 또는 일반 해석문을 요청받으면 현재 설치된 `$rq-wri`을 함께 사용한다. PIKACHU 경로에서는 그 실행순서를 바꾸지 않고 16번 안에 `POST_BOTTLENECK_RECOVERY_CANONICAL`을 삽입한다.
13. 형님 쌍둥이·240개·20D×12H·복수 문장 작업자를 요청받으면 `$rq-vedic-sentence-twin`을 함께 사용한다. 구조 Lock과 회수 Lock이 필요한 실제 문장 Job은 두 Lock이 확정되기 전 시작하지 않는다.
14. 템플릿 신규 제작·수정·검산·배치 확장에서는 `references/template-production-qa-lifecycle.md`를 전부 읽는다. 공통 수명주기 패킷을 만든 뒤 `python3 scripts/validate_template_lifecycle_packet.py <packet.json>`을 실행하고, 그 다음 선택 경로의 전용 검증기를 실행한다. 공통 검증기는 경로별 00A~00C·01~20·병목후 11관절 또는 독립 경로 토폴로지를 대신하지 않는다.
15. `STRUCTURAL_JOINT_DISCOVERY`의 칼끝문장 품질을 맞출 때만 `references/d10-h10-calibration-only.txt`를 전부 읽는다. 이 예시는 경계·WHY·확정성·과잉해석 차단의 문장력만 교정하며 `CONTENT_ORDER`, `SLOT_TITLE`, `CHART_VALUE`, `SENTENCE_SKELETON`을 어떤 Job에도 상속하지 않는다.

다른 스킬이 없거나 필요한 정본 참조를 읽을 수 없으면 그 기능만 `HOLD`한다. 비슷한 규칙을 기억으로 재구성하지 않는다.

## 작업 모드 선택

현재 질문으로 필요한 모드만 결합한다.

- `STRUCTURAL_JOINT_DISCOVERY`: D Rashi–N하우스의 20D 세로축×Target D H01~H12 가로축 구조관절 전수탐색
- `FIXED_KNIFE_SENTENCE_01_20_PATH`: 사용자가 지정한 고정 제목형 FNa98 칼끝문장 01~20 제작·검산
- `DEEP_DENSE_240H_COMMON_PATH`: PIKACHU 비의존 공용 템플로 20D×H01~H12의 정확히 240개 심층촘촘결 잠금문 제작·검산
- `TEMPLATE_BUILD`: 신규 템플릿·스키마·파일 패밀리 제작
- `TEMPLATE_REPAIR`: 기존 템플릿의 누락·순서·권한·형식 수정
- `STRUCTURE_ANALYSIS`: Source에서 구조관절·경로·병목·회수 판정
- `INTERPRETATION_WRITING`: 분석 Lock을 사람말 해석문·분석문·문장결로 실현
- `VALIDATION_ONLY`: 기존 파일·ZIP·문장·정본 일치 검산만 수행
- `BATCH_EXPANSION`: H01~H12, 20D, 20D×12H 확장

기존 여섯 모드는 `PIKACHU_CANONICAL_PATH`에 속한다. `STRUCTURAL_JOINT_DISCOVERY`, `FIXED_KNIFE_SENTENCE_01_20_PATH`, `DEEP_DENSE_240H_COMMON_PATH`는 각각 독립 모드며 서로 또는 PIKACHU 경로와 한 패킷으로 결합하지 않는다. 한 요청에 둘 이상이 필요하면 패킷·상태·검증 결과를 경로별로 나눈다.

검산 요청은 수정 권한을 포함하지 않는다. 수정·재작성 요청이 있을 때만 파일을 바꾼다.

## 실행 순서

### 0. 전역 Source 입장 게이트를 먼저 잠근다

모든 모드에서 실제 차트값·명령·예시·교차검산 근거로 쓰는 외부 Source에 다음 식을 가장 먼저 적용한다. 사용자가 승인한 내부 템플릿 스키마 자체는 차트 Source가 아니다.

```text
SOURCE_ADMITTED = SC_VERIFIED
               OR provider-native created_at >= 2026-08-09T00:00:00+09:00
```

경계시각을 포함한다. `created_at`은 timezone이 있는 원본 제공자 메타데이터여야 한다. `modified_at`, `updated_at`, 최근 열람일, 다운로드일, 로컬 mtime·ctime, ZIP 해제시각은 생성시각을 대체하지 못한다. SC가 아니어도 생성시각 분기를 통과하면 허용한다. 두 분기를 모두 실패한 Source는 제외하고, 그 Source가 필수이면 작업을 `HOLD`한다.

각 Source에 `sc_verified`, `sc_verification_basis`, `created_at`, `created_at_source`, `admission_basis`를 남긴다. 입장 통과는 `ACTIVE_CANONICAL`, `ACTIVE`, `PARSED`, Target 적용 권한을 자동으로 만들지 않는다.

### 1. 실제 질문과 Target을 잠근다

다음을 먼저 확정한다.

- `ACTUAL_QUESTION`
- `CURRENT_TARGET / DELIVERABLE`
- `TARGET / TARGET_DOMAIN / TARGET_FUNCTION`
- `ACTION / OPERATION_MODE`
- `SOURCE / SCOPE / EXCLUSIONS`
- `OUTPUT_CONTRACT / FORMAT / FILE_FAMILY`
- `IN_SCOPE_REQUIREMENTS / AUTHORIZATION_LINKS / STOP_CONDITION`

Source의 양이나 과거 작업이 현재 Target을 바꾸지 못한다. 확인할 수 없는 관절만 `HOLD`한다.

`STRUCTURAL_JOINT_DISCOVERY`라면 이 단계에서 `TEMPLATE_ID=DEEP_DENSE_KNIFE_SENTENCE_TEMPLATE_SET_V2`, `TEMPLATE_VERSION=V2_REPAIRED`, `TEMPLATE_AUTHORITY=ACTIVE_CANONICAL`, `CANONICAL_SCOPE=RQ_VEDIC_SYSTEM_WIDE_FOR_STRUCTURAL_JOINT_DISCOVERY`, `TARGET_D_CHART`, `TARGET_HOUSE=N`, `D_CHART_DOMAIN`, `HOUSE_FUNCTION`, `SOURCE_HOUSE_TOKEN`, `SOURCE_ROUTER_16`, `PIKACHU_DEPENDENCY=NOT_USED`를 잠근다. Rashi·Bhava·강도·외부 실행 게이트는 Router lane으로 분리하고 한 View로 병합하지 않는다. 하나라도 필수인데 확인되지 않으면 전수탐색을 시작하지 않는다. `FIXED_KNIFE_SENTENCE_01_20_PATH`라면 `TEMPLATE_ID=FIXED_KNIFE_SENTENCE_01_20_FNA98_V1`, 같은 Target 필드, `SOURCE_AUTHORITY=GOOGLE_DRIVE_ACTIVE_CANONICAL`, `CHART_VALUE_MODE=FETCH_FROM_DRIVE`, `UNVERIFIED_VALUE_GENERATION=FORBIDDEN`을 잠근다. `DEEP_DENSE_240H_COMMON_PATH`라면 `TEMPLATE_ID=DEEP_DENSE_LOCK_240H_COMMON_V1`, `SCOPE=20D×H01~H12=240 JOBS`, `PIKACHU_DEPENDENCY=NOT_USED`를 잠근다.

세 독립 경로는 여기서 분기한다. `STRUCTURAL_JOINT_DISCOVERY`는 V2의 `00_TARGET_LOCK→01_SOURCE_ROUTER_16→02_EVIDENCE_REGISTRY→03_STRUCTURAL_JOINT_DISCOVERY→04_JOINT_BANK→05_INDEPENDENT_ALLOCATION_01_20→06_HUMAN_SENTENCE_ASSEMBLY→07_SENTENCE_REVERSE_MAP→08_MINIMUM_FINAL_GATE`를 순서대로 실행한다. 각 01~20의 제목은 해당 Job의 관절 배정 뒤 동적으로 만들고 D10-H10 제목벡터를 복제하지 않는다. `FIXED_KNIFE_SENTENCE_01_20_PATH`는 `00_TARGET_LOCK→01_SOURCE_LOCK→02_SLOT_EVIDENCE_MAP_01_20→03_FIXED_SENTENCE_ASSEMBLY_01_20→04_SENTENCE_REVERSE_MAP→05_FIXED_PACKET_VALIDATION→06_FIXED_OUTPUT_VALIDATION→07_3PASS_FINAL_GATE`를 실행하며 고정 제목을 동적으로 바꾸지 않는다. `DEEP_DENSE_240H_COMMON_PATH`의 빈 템플 단계는 고정 제목 토폴로지만 검산해 닫고, 실제 Job 생성 때부터 각 Job의 Source·Structure·문장 검산을 실행한다. 아래 2~11의 PIKACHU 실행순서를 세 독립 경로에 끌어오지 않는다.

### 2. 사용자 정의 명령을 찾고 잠근다

현재 요청·정본·Source에 명령 토큰이 있거나 템플릿 family가 명령으로 작동하면 먼저 원문 정의를 찾는다. 현재 프로젝트 Source, 사용자 지정 파일, ACTIVE_CANONICAL 명령 레지스트리, 선행 Handoff를 검색해 다음을 `COMMAND_REGISTRY`로 만든다.

- 명령의 정확한 표기
- 사용자 정의 의미
- 권한·적용 범위·입력·출력
- 실행 순서와 선행조건
- 결합 가능 명령과 충돌 규칙
- 금지사항·HOLD 조건
- Source ID·원문 위치·상태

현재 질문에 필요한 기능만 결합한다. 명령이 Target을 바꾸게 하지 않는다. 사용자 정의가 확인되지 않으면 일반 AI 의미로 추정하거나 새 기능을 붙이지 않고 해당 명령만 `HOLD`한다.

### 3. 정본과 Source를 잠근다

`references/authority-and-states.md`의 우선순위와 상태축을 적용한다. 파일명만 보지 말고 원문 전체 또는 필요한 전 범위를 직접 읽는다. 각 Source에 `SOURCE_ID`, 경로·문서명, 권한, 상태, 읽은 범위, 해시 또는 동등한 식별값을 기록한다.

`ACTIVE_CANONICAL`이 교체되면 새 정본으로 패킷을 다시 만들고 이전 패킷·분석·문장·파생표를 자동 승계하지 않는다.

### 4. 차트 정체를 잠근다

최소한 다음을 분리한다.

- `D_CHART / D_CHART_DOMAIN`
- `HOUSE_ID / HOUSE_FUNCTION`
- `RASHI / BHAVA / OTHER VIEW`
- `SUBJECT / TIME BASIS / NODE TYPE / HOUSE METHOD` 중 Source에 있는 값
- `EMPTY / SINGLE / MULTI`

Rashi 값을 Bhava에 덮어쓰지 않는다. 도메인-하우스 번역을 먼저 확정한 뒤 차트값을 해석한다. 기본 20D는 `D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60`이다. `D50=VOID`이며 입력·대체·복구·Job 생성이 금지된다.

### 5. Source Snapshot을 만든다

필요한 범위에서 다음을 비가산 층으로 정리한다.

- Target sign·occupants·degree order
- House Lord와 Lord route
- co-presence·linked houses·additional required houses
- degree·Nakshatra/Pada·RL/NL/SL/SSL
- strength·support·pressure·aspect·state·timing·visibility·attribution 층

서로 다른 강도·권한·지원값을 하나의 점수로 합치지 않는다. Aspect는 배치 직후 압력지도와 강도 반영 후 판정으로 두 번 검문한다. Target에 적용되지 않는 층은 `NOT_APPLICABLE`, 자료는 있으나 아직 읽지 않은 층은 `NOT_PARSED`로 둔다.

Snapshot부터 최종 문장까지 `00A~00C`, `01~20`, `POST_01~POST_11`의 각 관절을 독립 셀로 채운다. 각 셀에는 `INPUT_REF→COMMAND→OPERATION→OUTPUT→HANDOFF→EVIDENCE_GRADE→STATUS`를 남긴다. 모든 관절에 확인된 사용자 명령을 배치하고, 앞 관절이 PASS 또는 정당한 NOT_APPLICABLE이 아니면 다음 관절로 진행하지 않는다.

20D 세로축과 Target D의 H01~H12 가로축은 선행 좌표지도에서 한 번만 계산한다. `00A~00C`를 쓰는 경로는 그곳에서 좌표를 잠그고, 이후 `ONE_D_CHART × ONE_HOUSE` 실행 셀은 좌표지도 ID와 판정만 인계받으며 20D 스캔을 반복하지 않는다. 00A~00C가 없는 독립 경로도 승인된 동등 단계에서 한 번만 잠근다.

### 6. 템플릿 또는 구조 Lock을 만든다

템플릿이면 파일명 패밀리 문법 → Source Classification → `R / A / D1 / Target / INDEX` → 선행 Handoff → Source Family Gate → 현재/이전 레이어 분리 → D1/Target 적용 규칙 → Missing/HOLD → 금지사항 → 검산 기준 → 검산 보고 → 최종 잠금문 → ending meta 순으로 설계한다.

템플릿 작업은 동시에 `Source Scope → File Family → Stage Role → Input Source → Source Separation → 12H/240 Job 배치 → Application Route → Raw Check → Link Check → Pilot → 3PASS → Final Output`의 공통 수명주기를 완주한다. 각 단계는 `INPUT_REFS→OPERATION→OUTPUT→HANDOFF→EVIDENCE_GRADE→STATUS`를 남긴다. 공통 패킷이 PASS한 뒤에만 선택 경로의 전용 토폴로지 PASS를 최종 판정에 결합한다.

기존 family를 수정할 때는 승인된 block명·순서·ending meta를 보존한다. placeholder는 값 종류·허용상태·Source 필드를 드러내는 typed placeholder로 만든다.

분석이면 `EVIDENCE_MAP`과 `STRUCTURE_LOCK`을 먼저 만든다. 사실·승인 규칙 파생·추론·HOLD를 분리하고, `원인→조건→매개→작동→변화→판정→결과`의 WHY 관절을 끊지 않는다.

### 7. 단일 하우스 파일럿을 통과시킨다

새 template family·새 문장 family·새 해석 방식은 지정된 한 Target의 선택 경로 전 순서 파일럿으로 먼저 검증한다. PIKACHU 경로는 00A~00C·01~20·병목후 11관절을, 독립 경로는 각자의 정본 토폴로지와 전용 검증기를 사용한다. 선택 경로 파일럿이 PASS한 뒤에만 12H·20D·다섯 작업탭으로 확장한다.

사용자가 검증된 동일 family의 즉시 확장을 명시한 경우에만 새 파일럿을 생략한다. 생략 근거를 작업패킷에 기록한다.

### 8. RQ18·RQ10을 필요한 작업에만 실행한다

구조 연결·병목·회수·최종 잔존을 다루면 `$rq-wri`의 현재 RQ18/RQ10 정본을 사용한다. 출력 전 다음 Lock을 확보한다.

- `MERGED_STRUCTURE_LOCK_ID / SHA256`
- `SEALING_AXIS_LOCK_ID / SHA256`
- `BOTTLENECK_CIRCUIT_LOCK_ID / SHA256`
- `POST_BOTTLENECK_RECOVERY_LOCK_ID / SHA256`

병목은 최초 유효 병목·지배 병목·2차 병목을 분리한다. 병목 위치를 확정한 뒤 `POST_BOTTLENECK_RECOVERY_CANONICAL`의 통제변수 추출→뒤집기→누수 차단→동일조건 재투입→대체경로 비교→회수량 재계산→BEFORE/AFTER 증명을 모두 끝낸 후에만 최종 잔존·회로 종료로 들어간다. 경로는 `SOURCE→SELECTED→PROCESSED→TRANSFERRED→ARRIVED→ATTRIBUTED→OWNED→RETAINED→USED→RETURNED→REINVESTED→FINAL_REMAINDER`를 검문한다. 기준값·단위가 없으면 회수량 증가를 수치로 만들지 않고 구조 증명 또는 `HOLD`로 둔다.

### 9. 해석문·분석문·3개 문장결을 실현한다

구조 분석과 문장 작성을 분리한다. 문장팀은 Structure Lock을 바꾸지 않는다.

- `도파민결`: 중심압·장면·핵심 대비를 즉시 잡되 인과와 경계를 줄이지 않는다.
- `심층작동결`: 주어·입력·변환·인계·출력·잔존의 작동회로를 드러낸다.
- `심층촘촘결`: 약 3.25~3.75단계 목관절층에서 조건·압력·반례·병목·귀속·누수·회수·예외를 촘촘히 봉합한다.

세 문장결을 요청받으면 같은 말을 길이만 늘려 복제하지 않는다. 제공된 3결 파일은 `GRAIN_STYLE_AUTHORITY=USER_CONFIRMED_REFERENCE`로 쓰되, 병목후 11관절 누락 때문에 완성 잠금문으로 보지 않는다. 같은 Source와 Structure Lock을 공유하되 각 결의 기능을 다르게 실현하고, 더 잘 쓸 때도 결의 기능·차트값·경계를 바꾸지 않는다. 일반 분석문도 근거 뒤에 WHY를 붙이고, Source에 없는 이유·감정·의도를 만들지 않는다.

### 10. 확장과 파일화를 실행한다

12H 확장은 선택 경로의 전체 순서를 House마다 보존한다. PIKACHU 경로만 `00A~00C→01~20`과 16번 내부 11관절을 사용하고, 동적 V2·고정 칼끝문장·240H 공용 경로는 각자의 토폴로지를 사용한다. 20D 기본 집합은 `D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60`이다. 한 House×20D도 각 `ONE_D_CHART × ONE_HOUSE` Job을 독립 완주한다. 각 D-chart의 고유 domain과 house 기능을 새로 잠그며 값을 평균화하거나 앞 하우스 문장을 치환하지 않는다.

사용자가 파일을 요청하거나 결과가 긴 경우 완성 파일로 납품한다. 기존 파일명·1 chart=1 file·ending meta 규칙이 지정되어 있으면 그대로 보존한다. ZIP 요청 시 내부 파일 존재·이름·수량·내용 끝·압축 해제 가능 여부를 확인한다.

### 11. 검산하고 최종본만 납품한다

`references/quality-gates.md`의 3PASS와 FNa98 게이트를 수행한다. 수정 가능한 결함은 내부에서 고친다. 필수 근거·권한·정본 충돌이 남으면 `HOLD`; Source는 있으나 수정 가능한 결함이면 `REVISE`; 모든 필수 게이트와 실제 저장 확인을 통과해야 `PASS`다.

템플릿 작업은 `validate_template_lifecycle_packet.py`와 선택 경로의 전용 검증기를 모두 통과해야 한다. 동적 V2는 `validate_structural_joint_packet.py`와 `validate_knife_sentence_v2_output.py`, 고정형은 `validate_fixed_knife_sentence_packet.py`와 `validate_fixed_knife_sentence_output.py`, 240H 공용형은 `validate_deep_dense_240h_template.py`를 사용한다. `PASS_WITH_BOUNDARY_NOTE`, `PASS_AFTER_PATCH`, `REVISE_REQUIRED` 같은 세부 납품표시는 각각 공통 상태 `PASS`, `PASS`, `REVISE`에 매핑하고, 경계 메모·패치 후 재검산 증거·수정 위치를 별도 필드에 남긴다.

초안·중간본·구조만 있는 본문으로 완료를 대신하지 않는다. 텍스트 표면의 구분선은 `━` 정확히 24칸으로 통일하고, 지정된 Gray codebox가 있으면 그 표면을 보존한다. 최종 사용자 응답은 완제품 결과, 파일 링크와 짧은 상태만 남기고 즉시 종료한다.

## 금지

- 기억·일반지식으로 정본 공백 채우기
- 정의를 찾지 못한 사용자 명령을 일반 의미로 실행하거나 새 기능 부여
- `VOID` 자료 참조·병합·복구·정본 승격
- Rashi/Bhava 또는 서로 다른 강도층 합산
- 한 하우스 문장을 다른 하우스에 placeholder 치환
- 20D 좌표 스캔을 각 `ONE_D×ONE_H` 실행 블록에서 반복
- D50을 기본 20D·대체 Manifest·240H Job에 삽입하거나 D5를 누락
- 현재 완제품과 직접 연결되지 않은 이전 미해결작업·다른 계보·유지보수·추가개선 자동 반입
- 24칸이 아닌 `━` 구분선을 최종 템플릿 표면에 사용
- 최신 PIKACHU×SC의 00A~00C·01~20을 과거 19층이나 임의 단계수로 교체
- 00A~00C·01~20·병목후 11관절 어느 곳에서든 사용자 명령을 빼거나 정의 없이 이름만 배치
- 미세 관절 셀을 합치거나 생략하고 키워드 나열·뜻풀이만으로 통과
- 미확인 파일·미실행 검산·미저장 산출물에 PASS 선언
- 문장 유창성으로 인과·귀속·회수량 창작
- 검산 요청만으로 원본 수정
- 동적 V2의 제목 생성·20 PRIMARY 배정을 고정형 경로에 적용하거나 고정 01~20 제목을 V2 전역순서로 역수출
- `rq-sc7`의 SC 검증을 Google Drive Active Canonical 승인이나 Transit 정본 승인으로 변환
- 나크파다 하위패킷의 Source·회로 PASS를 고정 칼끝문장 전체 PASS로 합치거나 다른 18개 슬롯을 덮어쓰기
