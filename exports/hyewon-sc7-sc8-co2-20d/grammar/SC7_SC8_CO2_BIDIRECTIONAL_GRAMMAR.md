# SC7 ↔ SC8 04 공동장 양방향 문법 역산

복원 호출키: `$rq-sc7-sc8-co2-grammar`

## 판정

**04 공동장의 공통 구조문법은 `PASS`, 현재 SC7 ↔ 현재 SC8의 무손실 양방향 컴파일은 `HOLD`다.**

20개 D차트를 `D → Rashi/Bhava/Comparison → House → Section → Block → Row → Field → Token`으로 결속했다. SC8의 `Rashi 240 + Bhava 240 + Comparison 240 = 720/720` 패킷, SC7의 활성 `Rashi 73 + Bhava 51 = 124/124` CO_FIELD anchor가 모두 공통문법을 통과했다.

그러나 현재 두 자료만으로 exact renderer를 만들면 다음 두 종류의 손실을 숨기게 된다.

1. SC8의 Bhava `CO2 Source Cross-check`는 현재 SC7의 활성 House 위치가 아니라 과거 BOX 위치·과거 member state를 보존한다.
2. SC8은 SC7의 Chart-Specific Role, £칸, €칸, Reality Rule, 운영문, VOID 기록, 수정시각과 provenance를 운반하지 않는다.

따라서 실행기는 구조 검증 JSON만 만들고, 정답처럼 보이는 TXT는 만들지 않는다. 수동 보정과 D별 치환표도 사용하지 않는다.

## Source 잠금

| 항목 | 잠금값 |
|---|---|
| Repository | `coco352748-jpg/352748angel` |
| Export branch | `exports/sc7-sc8-co2-20d` |
| SC7 | `07_4AB_D*_VeDic_CO2_Sc.txt` 20개 |
| SC8 | `04_*_D*_CoPreSeNcE_12H_AppLieD_R.txt` 20개 |
| Source family | `vedic_co2` / Rashi-Bhava co-presence field |
| 명시적 dependency | `rashi`, `bhava` |
| 활성 D | `D1, D9, D2, D3, D4, D5, D6, D7, D8, D10, D11, D12, D16, D20, D24, D27, D30, D40, D45, D60` |
| D50 | `VOID` |
| 03 Co-presence First | 04 문법에 병합 금지 |

SC7 Source family의 원본 SHA-256은 `b1b2a692695763d9f1648ddfd6e993d2f8eaa5290350c191530ad1c977433a91`이다. 분할된 20개 member는 이 Source의 D-section을 보존한다.

## 전수 결속 결과

| 결속 | 결과 |
|---|---:|
| SC8 Rashi packets | 240/240 PASS |
| SC8 Bhava packets | 240/240 PASS |
| SC8 Comparison packets | 240/240 PASS |
| SC8 전체 packets | 720/720 PASS |
| SC7 Rashi snapshot → SC8 Rashi occupant set | 240/240 PASS |
| SC7 Bhava distribution → SC8 Bhava occupant set | 240/240 PASS |
| Rashi EMPTY/SINGLE/CO-PRESENCE | 240/240 PASS |
| Bhava EMPTY/SINGLE/CO-PRESENCE | 240/240 PASS |
| Rashi↔Bhava comparison status | 240/240 PASS |
| 활성 Rashi CO_FIELD 위치 | 73/73 PASS |
| 활성 Bhava CO_FIELD 위치 | 51/51 PASS |

SC8 상태분포:

| Lane | EMPTY | SINGLE | CO-PRESENCE |
|---|---:|---:|---:|
| Rashi | 93 | 74 | 73 |
| Bhava | 105 | 76 | 59 |

Bhava의 59개 공동장은 다음 세 공급원을 구분한다.

- 현재 SC7 활성 Bhava CO_FIELD: 51개
- SC8이 과거 snapshot/BOX reference를 다시 연결한 슬롯: 7개
- Bhava House Distribution의 `Venus + Maandi`에서 직접 생긴 슬롯: 1개

마지막 두 종류를 현재 활성 CO_FIELD로 위장하지 않는다.

## D1과 Target 프로필

### D1 profile

- `R-1H~R-12H`, `B-1H~B-12H`, `C-1H~C-12H`
- 논리행 1,441, `《field》` row 632
- D1 전용 상태어: `MAINTAINED`, `PARTIAL_MAINTAINED_TO_SINGLE`, `RE-FUNCTIONED_SUPPORT_ONLY`, `SINGLE_MAINTAINED`, `NONE / LORD_ONLY`
- D1 Rahu/Ketu는 SC7 `24:58:08`과 SC8 canonical `26:33:09`가 다른 source state다.

### Target profile

- D9·D2~D60 각 문서에 R/B/C 36 packet
- 각 문서 논리행 1,548, `《field》` row 717
- Target 전용 상태어: `PARALLEL_CO_PRESENCE`, `RASHI_CO_FIELD_BHAVA_SPLIT_OR_SINGLE`, `BHAVA_CO_FIELD_ONLY`, `SINGLE_PARALLEL`, `MIXED_SINGLE_EMPTY`, `NONE / LORD_ONLY`
- D9 filename family는 `1A`, 나머지 Target은 `1B`다. 이는 파일 profile 규칙이지 값 변환용 차트 예외가 아니다.

## 공통 생성문법

### 1. 좌표와 Lane

각 D에서 House는 `1H → 12H` 순서다. 출력 lane은 반드시 `Rashi 12 → Bhava 12 → Comparison 12`다. Rashi와 Bhava는 서로 덮어쓰지 않으며 Comparison만 두 lane을 읽는다.

### 2. Rashi 원자화

SC7의 `Visible Rashi Chart Snapshot` 한 행을 planet/point token으로 분해한다.

- entity 0개 또는 명시적 `EMPTY` → `EMPTY`
- entity 1개 → `SINGLE`
- entity 2개 이상 → `CO-PRESENCE`

`As`는 `Lagna`, `Md`는 `Maandi`의 표기 alias로만 정규화한다. 값 계산이나 보이지 않는 entity 보충은 하지 않는다.

활성 Rashi CO_FIELD 73개는 snapshot의 동일 House entity set과 정확히 일치한다. 이 block에서 Field Type, Exactness, Independent Functions, Mutual Coloring을 읽되, snapshot의 planet order나 Rashi lane을 Bhava로 옮기지 않는다.

### 3. Bhava 원자화

SC7의 `Visible House Distribution`을 Rashi와 별도로 분해한다. Maandi/Md `SUPPORT_ONLY`도 보이는 point이므로 cardinality에는 포함하지만 classical core로 승격하지 않는다.

- 0 entity → `EMPTY`
- 1 entity → `SINGLE`
- 2 entity 이상 → `CO-PRESENCE`

이 규칙은 SC8 Bhava 240/240과 일치한다. 활성 Bhava CO_FIELD 51개는 해당 House의 core 설명을 공급한다. House Distribution에만 있는 support member는 별도 support token으로 덧붙일 수 있지만, CO_FIELD core member를 삭제하거나 support를 core로 바꾸지 않는다.

### 4. Comparison 상태문

Target profile의 비교상태는 Rashi/Bhava의 effective cardinality만으로 다음처럼 결정된다.

| Rashi | Bhava | Target comparison |
|---|---|---|
| CO | CO | `PARALLEL_CO_PRESENCE` |
| CO | SINGLE 또는 EMPTY | `RASHI_CO_FIELD_BHAVA_SPLIT_OR_SINGLE` |
| SINGLE 또는 EMPTY | CO | `BHAVA_CO_FIELD_ONLY` |
| SINGLE | SINGLE | `SINGLE_PARALLEL` |
| SINGLE | EMPTY 또는 EMPTY | SINGLE | `MIXED_SINGLE_EMPTY` |
| EMPTY | EMPTY | `NONE / LORD_ONLY` |

D1은 별도 profile이다.

| Rashi | Bhava | D1 comparison |
|---|---|---|
| CO | CO | `MAINTAINED` |
| CO | SINGLE | `PARTIAL_MAINTAINED_TO_SINGLE` |
| SINGLE | SINGLE core | `SINGLE_MAINTAINED` |
| SINGLE | SUPPORT_ONLY | `RE-FUNCTIONED_SUPPORT_ONLY` |
| EMPTY | EMPTY | `NONE / LORD_ONLY` |

이 두 표는 240/240 comparison packet을 재현한다.

### 5. Planet packet과 순서

- 입력에 보이는 degree order만 사용한다.
- `Planet A`, `Planet B`, `Planet C`, `Additional Planet`은 해당 profile의 고정 row 위치에 둔다.
- degree order는 시간순서나 인과순서가 아니다.
- Gap/Exactness가 Source에 없으면 계산해 채우지 않고 `NOT_SHOWN`, `NONE`, `HOLD` 중 Source가 지정한 상태를 유지한다.
- Rashi exactness와 Bhava placement를 한 값으로 합치지 않는다.

### 6. House Function·Lord·Priority

House Function의 고정어와 row 위치는 첨부 template specification에서 읽을 수 있다. 그러나 House Lord, Lord Position, RL/NL/SL/SSL, Priority와 일부 고정 해석문은 현재 04 SC7만으로 전부 명시되지 않는다. 이 값은 `rashi`/`bhava` dependency가 같은 source state로 공급될 때만 채운다. 조티시 일반론으로 계산하지 않는다.

### 7. EMPTY·HOLD·VOID

- `EMPTY`: 해당 lane의 명시적 빈 House
- `SINGLE`: entity는 있으나 공동장 아님
- `HOLD`: Source 또는 exact carrier가 부족해 결정 불가
- `VOID`: 이전 snapshot/BOX record로, 활성 House record가 아님
- `N.A.`와 `NOT_SHOWN`은 서로 바꾸지 않음

SC8이 과거 BOX를 참조하더라도 현재 SC7의 VOID를 임의 해제하지 않는다.

### 8. 제목·섹션·고정문

첨부 4개 template는 field 사전·조건·순서를 제공하는 typed specification이다. 실제 Applied 문서와 byte-equal한 skeleton은 아니다.

| Template | 논리행 | field rows | Applied와 byte-equal |
|---|---:|---:|---|
| `04_1A_D1_12H_CO2_TemPL_.txt` | 1,426 | 632 | 아니오 |
| `04_1A_D1_CO2_12HouSe_TeMpl_♤.txt` | 1,679 | 632 | 아니오 |
| `04_1B_CO2_12H_TEMpL_.txt` | 1,425 | 632 | 아니오 |
| `04_2B_TaRgEt_CO2_12HouSe_TeMpl_A♤.txt` | 1,940 | 743 | 아니오 |

따라서 placeholder를 임의의 SC8 과거값으로 채워 exact target이라고 선언하지 않는다.

## exact forward가 HOLD인 이유

Target 19개 D에서 현재 활성 Bhava CO_FIELD 48개와 SC8 cross-check를 비교했다.

| 검사 | 결과 |
|---|---:|
| 현재 활성 House location exact | 0/48 |
| current member set exact | 41/48 |
| current member가 SC8 set의 subset | 45/48 |
| true member conflict | 3/48 |

SC8의 `CO2 Bhava Location`은 대체로 `BOX_*` 과거 위치를 쓴다. 이 과거 위치를 현재 SC7 House에서 차트별 lookup으로 되살리는 것은 공통문법이 아니다. 또한 D1 Rahu/Ketu의 source state가 다르다. 따라서 `Forward(current SC7) = paired SC8 bytes`를 source-backed rule로 증명할 수 없다.

## exact reverse가 HOLD인 이유

SC8에는 다음 SC7 carrier가 없다. 아래 621건은 역복원 불가를 증명하는 보수적 witness이며 전체 손실의 상한·하한을 뜻하지 않는다.

| SC7-only carrier | SC8 미운반 occurrence |
|---|---:|
| Chart-Specific Role | 133 |
| £칸 | 103 |
| €칸 header | 103 |
| Reality Rule | 133 |
| D별 Operating Note | 20 |
| Previous Bhava VOID section | 20 |
| VOID Verdict | 29 |
| Previous Single-Field Index | 20 |
| Source Modified timestamp | 40 |
| Final Authority header | 20 |

SC8 reference 파일을 정답 lookup으로 사용해 이 문장을 다시 붙이면 reverse compiler가 아니라 답안 재생기다. 실행기에서 금지한다.

## 양방향 불변식 판정

요구식:

\[
F(x)=y,\quad R(y)=x,\quad R(F(x))=x,\quad F(R(y))=y
\]

현재 판정:

- 좌표·Lane·packet order: `PASS`
- occupant entity와 EMPTY/SINGLE/CO state: `PASS`
- comparison state: `PASS`
- 현재 SC7 → paired SC8 exact bytes: `HOLD`
- paired SC8 → 현재 SC7 exact bytes: `HOLD`
- byte roundtrip: `HOLD`

## 실행기

정방향 감사:

```bash
./forward_sc7_to_sc8_co2 \
  --sc7-root ../SC7 \
  --sc8-reference-root ../SC8 \
  --template-dir ../templates
```

역방향 감사:

```bash
./reverse_sc8_to_sc7_co2 \
  --sc7-root ../SC7 \
  --sc8-reference-root ../SC8 \
  --template-dir ../templates
```

정상 Source에서도 exact gate가 닫혀 있으므로 `status=HOLD`, 종료코드 2다. CI 구조감사에는 `--allow-hold`를 쓸 수 있으나 JSON 상태는 HOLD 그대로다. 누락·중복·D50·파싱 오류는 `--allow-hold`로도 종료코드 2이며 TXT는 생성하지 않는다.

## HOLD 해제 조건

다음 중 하나가 필요하다.

1. paired SC8과 같은 시점의 pre-rewrite SC7 Bhava BOX/CO2 Source 및 D1 node source를 공급한다.
2. 현재 SC7을 정본으로 한 새 SC8 04 Applied를 생성하고 기존 SC8은 역사본으로 분리한다.
3. SC8에 SC7-only control/VOID/provenance와 source-state version을 담는 무손실 inverse carrier를 추가한다.
4. `rashi`/`bhava` dependency의 exact snapshot과 고정문 profile version을 함께 잠근다.

그 전에는 차트별 예외, 과거값 lookup, 수동 보정 없이 HOLD를 유지한다.

## 최종 상태

- 공통 04 공동장 구조문법: `PASS`
- 720 packet 결속: `720/720 PASS`
- 활성 SC7 CO_FIELD 결속: `124/124 PASS`
- 수동 보정: `0`
- 차트 ID 기반 값 예외: `0`
- Rashi/Bhava 상호 덮어쓰기: `0`
- target-looking TXT 생성: `0`
- exact forward/reverse/roundtrip: `HOLD`

상세 전수값은 `roundtrip_co2_coverage.json`, 미해결 관절만은 `co2_grammar_hold_registry.json`에 기록한다.
