# RQ Vedic 분석 연산자 계약

`CONTRACT_ID=RQ_VEDIC_ANALYSIS_OPERATORS_V1`

이 파일은 `$rq-vedic` 본체의 하위 메뉴·규칙 구축·차트 실행에 적용한다. 연산자는 새로운 Source나 점성학 법칙을 만들지 않는다. 기존 `STRUCTURE → EXTRACT → ASSUMPTIONS → TRACE → FACTCHECK → SYNTHESIZE` 안전축을 유지하고, 현재 Target에 필요한 연산자만 추가한다.

## 공통 실행경계

1. 명시 호출은 자동선택보다 우선한다.
2. 동일 철자·대소문자·별칭을 invocation record에 보존한다.
3. 연산자의 출력권한은 실행 중인 수준의 claim ceiling을 넘지 못한다.
   - `ELIVEDIC`: 직접값·경계·미상만
   - `ELICOLLEGE`: 패턴후보·대조·예외·구조해석까지
   - `ELIPHD`: Source와 관절이 닫힌 인과·귀속·회수·최종 해석까지
4. 연산자가 요구하는 근거가 없으면 결과를 생성하지 않고 해당 연산자 결과만 `HOLD`한다.
5. 연산자 실행이 D-chart·House·Module·Source 범위를 자동 확장하지 않는다.

## EXPAND /expand

기존 내용을 보존하면서 설명 근거 사례 배경 맥락을 추가한다.

확인되지 않은 정보를 사실처럼 채우거나 원래 범위를 무단 확장하지 않는다.

필수 출력:

`preserved_content, added_explanations, added_evidence, added_cases, added_background, added_context, unchanged_invariants, rejected_expansions`

경계:

- 추가 사례는 `CASE_AND_COUNTEREXAMPLE_BANK`의 exact case ref가 있을 때만 사실사례로 쓴다.
- 예시를 새로 만든 경우 `ILLUSTRATIVE_EXAMPLE`로 표시하고 실제 검증사례로 승격하지 않는다.
- 원래 claim의 강도·범위·예외를 확대하지 않는다.

## EXPLAIN

개념 원인 작동방식과 이유를 이해할 수 있도록 설명한다.

결과만 반복하지 않고 근거에서 결과까지의 연결을 보여준다.

필수 출력:

`concept, evidence, cause_or_condition, mechanism, change, judgment, result, limits`

## IMPLICATIONS

확인된 구조가 이후 단계에 만들어내는 함의 파급효과 후속결과를 분석한다.

직접 증거와 조건부 영향을 구분한다.

필수 출력:

`confirmed_structure, direct_implications, conditional_implications, downstream_layers, required_conditions, disconfirming_signals, evidence_refs`

경계:

- 함의를 새 사건예측으로 승격하지 않는다.
- 시간 함의에는 Dasha·Timing Gate·Ava2·Transit의 exact Source와 기준시점이 필요하다.

## IMPLICITPREMISES

Source와 논리구조 안에 실제로 깔려 있지만 문장으로 드러나지 않은 필수 전제를 복원한다.

그 전제가 없을 때 현재 결론이 성립하는지도 검사한다.

필수 출력:

`premises, source_or_logic_basis, necessity_tests, conclusion_survival, impact_if_false`

## INFER

직접 쓰여 있지 않은 의미를 확인된 근거와 관계에서 제한적으로 추론한다.

추론결과를 Source 직접 확인값으로 승격하지 않는다.

필수 출력:

`basis, relation, inference, authority=INFERENCE, uncertainty, falsifier`

## INNERARCHITECTURE

겉으로 드러난 결과를 만드는 내부 배치와 작동구조를 밝힌다.

내부 주어 전달경로 변환지점 승인권 병목 귀속 회수경로를 구분한다.

필수 출력:

`internal_subjects, transfer_paths, transform_points, approval_rights, bottlenecks, attribution, recovery_paths, residual`

## INTERPRET

확인된 자료와 구조가 실제로 무엇을 의미하는지 해석한다.

Source에 없는 사건이나 성격을 임의로 생성하지 않는다.

필수 출력:

`source_refs, confirmed_structure, meaning, application_boundary, unsupported_events_rejected`

## INVARIANTS

분해 번역 개선 재작성 뒤에도 변하면 안 되는 값을 불변조건으로 확정한다.

주어 대상 수치 순서 권한 귀속권 핵심 의미 인과관계를 잠근다.

필수 출력:

`subjects, targets, values, order, authorities, attribution_rights, core_meaning, causal_relations`

## ITERATE

결과를 검토 수정 재검증하는 과정을 반복한다.

새로운 정보가 없는데 형식만 계속 바꾸는 무한 반복은 중단조건을 둔다.

필수 출력:

`iteration_goal, input_version, defect, correction, verification, output_version, stop_condition`

중단조건:

- 요청 완료조건과 FNa98 게이트가 통과함
- 다음 반복이 새 근거·새 교정 없이 표현만 바꿈
- 필수 Source·권한이 없어 더 이상 안전한 수정이 불가능함

## KEYPOINTS /keypoints

전체 내용에서 판단과 이해에 가장 중요한 핵심 항목을 골라낸다.

핵심 선정기준이 없으면 작업자의 임의선택이 개입할 수 있다.

필수 출력:

`selection_criteria, selected_points, evidence_refs, excluded_points, exclusion_reasons, decision_impact`

기본 선정기준:

`Target 직접영향 → Source 권위 → 구조의 단일 실패지점 → 후속판정 변화량 → 예외·HOLD 영향`

수치·단위가 없으면 변화량을 임의 점수로 만들지 않고 구조 영향으로 비교한다.

## LAYER

자료와 작동을 출처 기능 단계 권한이 다른 독립 층으로 분리한다.

각 층을 연결할 수는 있지만 값과 판정권한을 자동 병합하지 않는다.

필수 출력:

`layers, sources, functions, stages, authorities, non_merge_rules`

## LAYERBOUNDARY

각 레이어가 설명할 수 있는 범위와 설명할 수 없는 범위를 고정한다.

작용 이동 도착 귀속 회수 현실층의 값이 서로 대체되지 않게 한다.

필수 출력:

`layer_limits, allowed_claims, forbidden_claims, forbidden_substitutions, handoff_rules`

## LAYERMAP

대상을 여러 독립 레이어로 나누고 각 레이어의 구성원 기능 관계를 배치한다.

레이어 간 연결은 표시하되 서로 다른 값을 하나로 합치지 않는다.

필수 출력:

`layer_nodes, members, functions, authorities, intra_layer_relations, inter_layer_handoffs, conflicts, non_merge_rules`

## IN_PROGRESS

`IN_PROGRESS`는 연산자가 아니라 실행상태다.

작업이 시작돼 진행 중이지만 완료조건을 아직 모두 충족하지 않은 상태다. 부분 산출물이 존재하더라도 `COMPLETE`로 승격하지 않는다.

필수 상태 필드:

`started=true, completed_conditions[], remaining_conditions[], blocking_conditions[], last_verified_artifact, next_executable_joint`

`IN_PROGRESS`를 `HOLD`와 바꾸지 않는다. 실행 가능한 다음 단계가 남아 있으면 `IN_PROGRESS`, 필수 근거·권한이 없어 확정할 수 없으면 그 관절은 `HOLD`다. 두 상태는 서로 다른 축에 동시에 존재할 수 있다.

## 조립 route

- 보존 확장: `INVARIANTS → EXPAND → FACTCHECK`
- 이해 설명: `EXPLAIN → KEYPOINTS`
- 함의 분석: `TRACE → IMPLICATIONS → FACTCHECK`
- 숨은 전제: `IMPLICITPREMISES → ASSUMPTIONS → INFER`
- 내부 구조: `LAYER → LAYERBOUNDARY → LAYERMAP → INNERARCHITECTURE → TRACE`
- 의미 해석: `INTERPRET`
- 반복 개선: `ITERATE → FACTCHECK → FNa98_GATE`

명시 호출이 여러 개면 현재 Target에 필요한 route만 결합하고 동일 연산을 중복 실행하지 않는다.
