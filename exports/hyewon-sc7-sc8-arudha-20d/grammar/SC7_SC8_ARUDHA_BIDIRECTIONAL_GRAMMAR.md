# SC7 ↔ SC8 Arudha 양방향 문법 역산

복원 호출키: `$rq-sc7-sc8-arudha-grammar`

## 판정

**아루다 공통 구조문법은 `PASS`, 기존 SC7 ↔ 기존 SC8의 무손실 양방향 컴파일은 `HOLD`다.**

SC7 통합 Source와 SC8 PIKACHU 20개 파일을 `D → House/UL → Section → Block → Row → Field → Token`으로 결속했다. `20D × 12H = 240` House와 독립 `UL 20`을 합친 **260/260 point가 모두 존재**하며, D1/Target 분리·House→A-point 매핑·landing 복제·SAME/DIFFERENT 판정·A12 HOLD·UL 독립 규칙은 SC7과 SC8 양쪽에서 전수 통과했다.

그러나 두 자료는 같은 상태의 전후 직렬화가 아니다.

- SC7 `07_6AB_AruDha_Sc.txt`는 `SCREENSHOT_MASTER_SOURCE_VERIFIED`가 반영된 후속 교정 통합본이다.
- SC8 PIKACHU의 20개 Arudha member는 그보다 앞선 값·상태를 보존한다.
- 같은 field schema 260/260은 유지되지만, point 122/260에서 값이 다르다.
- 6,645개 point field occurrence 중 5,971개는 같고 674개는 다르다.
- 20개 문서 중 byte-identical 대응은 0개다.

따라서 SC7의 교정값을 SC8의 옛값으로 되돌리는 규칙이나, SC8의 옛값에서 SC7 교정값을 복원하는 규칙을 만들면 차트별 과거값 lookup이 된다. 이는 공통문법이 아니라 금지된 차트 ID 하드코딩이다.

## Source 잠금

| 항목 | 잠금값 |
|---|---|
| Repository | `coco352748-jpg/352748angel` |
| Export branch | `exports/sc7-sc8-arudha-20d` |
| SC7 통합 Source | `07_6AB_AruDha_Sc.txt` |
| SC7 SHA-256 | `4ed64718172c0f570371378e3a215f12d9f2f92c40298912ca7205e282a64414` |
| SC7 내부 구성 | INDEX 1 + D-chart member 20 |
| SC8 대응 | PIKACHU canonical Arudha member 20 |
| D1 템플릿 | `06A_D1_ARUDHA_TEMPLATE_♤.txt` |
| D1 템플릿 SHA-256 | `d58f74fc853b670f8c0e23b20a33e02fc036a128b00d6687e45cdb76b0c12c57` |
| Target 템플릿 | `06B_TARGET_ARUDHA_TEMPLATE_♤.txt` |
| Target 템플릿 SHA-256 | `efd3ea70c804af11ae62351add8f3dca69be41942fcb83547a185f3910721ffb` |

활성 D 순서:

`D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60`

`D50=VOID`이며 어떤 Source·Job·대체 D로도 삽입하지 않는다.

## 좌표와 프로필

### D1 06A

- `1H AL/A1`부터 `12H A12`까지 12개 Surface Slot
- `A12 = HOLD_A12_INDEPENDENT_NOT_VISIBLE`
- `UL`은 A12와 분리된 독립 슬롯
- Target식 `17-*` section 없음
- Rashi/Bhava는 비교 anchor일 뿐 Arudha가 덮어쓰지 않음

### Target 06B

- D9·D2~D60의 Target-native Arudha
- 전체 D-Structure Source Board와 `17-1H`~`17-12H` packet
- `17-UL` 독립 packet
- `H1 → D-AL`, `H2 → D-A2`, …, `H12 → D-A12`
- Source House와 Pada Landing House를 별도 field로 유지

D9 파일명의 `1A`와 나머지 Target 파일명의 `1B`는 SC7 INDEX의 명시적 FILE NAMING RULE에서 읽는다. 이는 값 변환용 차트 ID 예외가 아니다.

## 공통 생성문법

### 1. Point 선택

- D1: `H1 → AL/A1`, `H2~H12 → A2~A12`, `UL → UL`
- Target: `H1 → D-AL`, `H2~H12 → D-A2~D-A12`, `UL → D-UL`
- House 순서는 1→12, UL은 마지막 독립 위치다.

검증 결과:

- D1 House→Pada: SC7 12/12, SC8 12/12
- Target House→Point: SC7 228/228, SC8 228/228

### 2. Position과 Landing

Source가 명시한 point의 Sign·Degree·Nakshatra/Pada·House를 보존한다. Target profile에서는 같은 값이 다음 세 field에 반복된다.

- `Arudha Sign` → `Pada Landing Sign`
- `Arudha House From Target D-Chart Lagna` → `Pada Landing House From Lagna`
- `Sign / House` → `Landing House Surface Channel`

이 복제 규칙은 적용 가능한 H1~H11에서 SC7 209/209, SC8 209/209 통과했다.

### 3. Source-Landing Status

`Source House of Pada == Pada Landing House`이면 `SAME_HOUSE`, 다르면 `DIFFERENT_HOUSE`다. 이 규칙은 SC7 209/209, SC8 209/209 통과했다.

Degree나 House를 이 상태문에서 역계산하지 않는다. 상태문은 source position의 checksum이다.

### 4. A12와 UL

- 독립 A12가 보이지 않으면 `HOLD_A12_INDEPENDENT_NOT_VISIBLE`을 유지한다.
- 화면의 UL을 A12로 쓰지 않는다.
- UL은 D1 `UL` 또는 Target `17-UL`에만 기록한다.
- A7·A12·UL은 서로 병합하지 않는다.

A12 HOLD와 UL 독립은 SC7 20/20, SC8 20/20 각각 통과했다.

### 5. Rashi·Bhava 경계

- Target Rashi/Bhava는 Actual Structure anchor다.
- Arudha는 Surface Structure다.
- `Target Rashi Link`, `Target Bhava Link`, `D1 Rashi Anchor`, `D1 Bhava Anchor`는 참조 field로만 둔다.
- Arudha 값이 Rashi/Bhava 위치나 사건 약속을 교체하지 않는다.
- Rashi/Bhava가 없으면 비교 status를 HOLD하고 Arudha point 자체를 제거하지 않는다.

### 6. 상태문과 고정문

다음은 position source에서 파생하거나 고정 프로필에서 생성할 수 있다.

- `Relevant Arudha Point`
- `Source-Landing Status`
- `Landing House Surface Channel`
- A12 HOLD 문장
- UL 독립 문장
- D1 import 금지·Rashi/Bhava overwrite 금지·surface only 문장

반대로 `Source Status`, `Completion Grade`, terminal `STATUS`, 화면 교정 완료 여부는 source state다. 다른 버전의 고정문으로 바꾸지 않는다.

## 템플릿의 역할

첨부된 06A·06B는 실제 Applied 문서의 byte skeleton이 아니라 typed grammar specification이다.

| 템플릿 | 줄 수 | placeholder | 적용문서와 byte-equal |
|---|---:|---:|---|
| 06A D1 | 1,089 | 355 | 아니오 |
| 06B Target | 2,789 | 524 | 아니오 |

따라서 템플릿은 field 사전·조건·경계·출력 순서를 정의하는 근거로 사용한다. 기존 SC8 문서를 값만 채워 재현하는 skeleton으로 사용하지 않는다.

## 실제 차이

같은 point field schema는 260/260이지만 다음 값이 다르다.

| Field | 불일치 occurrence |
|---|---:|
| Arudha Degree | 103 |
| Arudha Nakshatra/Pada | 100 |
| Arudha Sign | 82 |
| Arudha House | 82 |
| Pada Landing Sign | 82 |
| Pada Landing House | 82 |
| Landing House Surface Channel | 82 |
| Source-Landing Status | 11 |
| D1 Surface Visibility | 11 |
| D1 Use Decision | 12 |
| UL Sign/House/Degree/Nakshatra | 27 |

D1에서 SC7은 AL~A11과 UL Degree를 보존하지만 SC8은 `not shown`으로 직렬화한다. 이 12개 Degree는 SC8만으로 역복원할 수 없다.

D4~D11의 여러 point는 Sign·House·Degree·Nakshatra가 함께 바뀌었다. 단순 명칭 변환이나 고정 offset이 아니므로 공통 산술식으로 옛값을 만들지 않는다.

## 역방향 불변식 판정

요구식:

\[
F(x)=y,\quad R(y)=x,\quad R(F(x))=x,\quad F(R(y))=y
\]

현재 결과:

- 좌표·profile·field schema: `PASS`
- 공통 문법 조건: `PASS`
- SC7 현재값 → 기존 SC8 bytes: `HOLD`
- 기존 SC8 → SC7 교정값: `HOLD`
- byte roundtrip: `HOLD`

SC8에서 사라진 교정값을 SC7 reference 파일 lookup으로 돌려놓는 것은 역컴파일이 아니다. 대응 정답 파일 재생이므로 실행기에서 금지한다.

## 실행기

정방향 감사:

```bash
./forward_sc7_to_sc8_arudha \
  --sc7-source ../SC7/07_6AB_AruDha_Sc.txt \
  --sc8-reference-root ../SC8 \
  --template-d1 '../templates/06A_D1_ARUDHA_TEMPLATE_♤.txt' \
  --template-target '../templates/06B_TARGET_ARUDHA_TEMPLATE_♤.txt'
```

역방향 감사:

```bash
./reverse_sc8_to_sc7_arudha \
  --sc7-source ../SC7/07_6AB_AruDha_Sc.txt \
  --sc8-reference-root ../SC8 \
  --template-d1 '../templates/06A_D1_ARUDHA_TEMPLATE_♤.txt' \
  --template-target '../templates/06B_TARGET_ARUDHA_TEMPLATE_♤.txt'
```

현재는 정확 TXT를 만들지 않고 `status=HOLD`, 종료코드 2를 반환한다. `--allow-hold`는 CI 감사에서 종료코드만 0으로 바꾸며 상태를 PASS로 승격하지 않는다.

## HOLD 해제 조건

다음 중 하나의 정본 선택이 필요하다.

1. **현재 SC7 교정값을 기준으로 새 SC8 06A/06B Applied 정본을 생성**하고, 기존 SC8은 역사본으로 분리한다.
2. 기존 SC8을 목표로 유지하려면 **그 SC8과 같은 시점의 pre-correction SC7 Source**를 공급한다.
3. 양방향 무손실 carrier를 새 SC8 profile에 명시적으로 추가한다. 이 경우 기존 SC8 bytes와는 다른 새 버전이 된다.

그 전에는 옛값 lookup·D별 치환표·수동 보정 없이 `HOLD`를 유지한다.

## 최종 상태

- 공통 Arudha 구조문법: `PASS`
- 240H 결속: `240/240 PASS`
- UL 결속: `20/20 PASS`
- 수동 보정: `0`
- 차트 ID 기반 값 예외: `0`
- 기존 SC7 ↔ 기존 SC8 exact forward/reverse: `HOLD`
- 전체 byte roundtrip: `HOLD`

상세 전수값은 `roundtrip_arudha_coverage.json`, 미해결 관절은 `arudha_grammar_hold_registry.json`에 기록한다.
