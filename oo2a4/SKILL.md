---
name: oo2a4
description: SC8의 04번 Vedic CO2 Rashi–Bhava 공동장 정본을 원문 그대로 즉시 공급한다. 사용자가 $oo2a4, OO2A4, SC8 04번, 4AB 공동장, 특정 D차트·하우스의 Rashi/Bhava 공동장 또는 OO2A4 240H를 요청할 때 사용한다. 이동판정·NAK·SC3나 다른 SC8 번호는 자동 병합하지 않는다.
---

# OO2A4 — SC8 04 Direct Copy

## 고정 정의

`$oo2a4 = $rq-sc8-4ab`의 04번 Source를 byte 그대로 보유하는 독립 호출키다.

- Source archive: `assets/sc8-04/07_4AB_VeDic_CO2_Sc_.zip`
- Source scope: 20D별 Rashi/Bhava 12H 원본과 Vedic CO2 공동장 정본
- 구성: 20D member × 각 D의 12H Rashi/Bhava pair
- D 순서: `D1,D9,D2,D3,D4,D5,D6,D7,D8,D10,D11,D12,D16,D20,D24,D27,D30,D40,D45,D60`
- D50: `VOID`
- 권한: SC8 04 Source 공급만 수행한다. 새 공동장값·이동값·해석문을 만들지 않는다.

## 호출

인수 없는 `$oo2a4`은 고정 정의와 20D member 목록을 공급한다.

```bash
python3 scripts/oo2a4.py list
```

특정 D 전체 04번 원문:

```bash
python3 scripts/oo2a4.py read --dchart D11
```

특정 D×H는 같은 D member 안의 Rashi 12H 해당 행, Rashi 공동장 block, Bhava 12H 해당 행, Bhava 공동장 block을 Source substring으로 분리 공급한다. 해당 House에 공동장 block이 없으면 원본 행은 유지하고 `NO_MATCHING_CO_FIELD_BLOCK_IN_SOURCE`로 표시한다.

```bash
python3 scripts/oo2a4.py read --dchart D11 --house H05
```

`$oo2a4 240H`는 20D member를 고정 D 순서로 전부 연다. 각 member에 12H Rashi/Bhava pair가 있으므로 값을 재계산하거나 새 240 manifest를 만들지 않는다.

```bash
python3 scripts/oo2a4.py export
```

사용자가 검증을 명시하거나 Source가 바뀐 경우에만 다음을 실행한다.

```bash
python3 scripts/oo2a4.py verify
```

## 보존 경계

- ZIP 파일명·member명·본문·대소문자·수치·상태문을 바꾸지 않는다.
- Rashi 공동장과 Bhava 공동장을 합치거나 서로 대체하지 않는다.
- `$rq-sc8-3ab` 이동·변화판정을 앞에서 자동 호출하거나 04 Source 안에 병합하지 않는다.
- `$rq-sc8-4ak` Shadbala·Drishti·Aspect01을 같은 04번으로 취급하지 않는다.
- OO2·OO2A2·OO2B2·NAK·SC3를 자동 결속하지 않는다.
- SC7이나 일반 조티시 지식으로 공백·HOLD를 보충하지 않는다.
- Source 안의 `VOID`, `HOLD`, `N.A.`, `SOURCE_SCOPE_EXCLUDED`, `SUPPORT_ONLY`를 그대로 보존한다.
- 단독 호출에서 해석·사건·시기·귀속·보유·회수 판정을 실행하지 않는다.

Source 동일성이나 구성 검문이 필요할 때만 `references/source-manifest.json`을 읽는다.
