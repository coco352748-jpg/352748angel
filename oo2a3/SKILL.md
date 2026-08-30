---
name: oo2a3
description: SC8의 03번 Rashi–Bhava 이동·공동장 변화 검산과 03B 12하우스 First Integration 정본을 원문 그대로 즉시 공급한다. 사용자가 $oo2a3, OO2A3, SC8 03번, 3AB 이동판정, 특정 D차트·하우스의 03A/03B 또는 OO2A3 240H를 요청할 때 사용한다. 다른 SC8 번호나 OO2·NAK 층은 자동 병합하지 않는다.
---

# OO2A3 — SC8 03 Direct Copy

## 고정 정의

`$oo2a3 = $rq-sc8-3ab`의 03번 Source를 byte 그대로 보유하는 독립 호출키다.

- Source archive: `assets/sc8-03/07_3AB_CO2_First_p_Sc.zip`
- Source scope: `03A Rashi/Bhava Transfer and Co-presence Change Check + 03B 12-House First Integration`
- 구성: 20D member × 각 D의 12H 슬롯
- D 순서: `D1,D9,D2,D3,D4,D5,D6,D7,D8,D10,D11,D12,D16,D20,D24,D27,D30,D40,D45,D60`
- D50: `VOID`
- 권한: SC8 03 Source 공급만 수행한다. 새 이동값·공동장값·해석문을 만들지 않는다.

## 호출

인수 없는 `$oo2a3`은 고정 정의와 20D member 목록을 공급한다.

```bash
python3 scripts/oo2a3.py list
```

특정 D 전체 03번 원문:

```bash
python3 scripts/oo2a3.py read --dchart D11
```

특정 D×H는 같은 D member 안의 `03A-1` 해당 House 이동행과 `03B-<H>` 슬롯을 원문 substring으로 함께 공급한다.

```bash
python3 scripts/oo2a3.py read --dchart D11 --house H05
```

`$oo2a3 240H`는 20D member를 고정 D 순서로 전부 연다. 이미 각 member에 12H가 있으므로 값을 재계산하거나 새 240 manifest를 만들지 않는다.

```bash
python3 scripts/oo2a3.py export
```

사용자가 검증을 명시하거나 Source가 바뀐 경우에만 다음을 실행한다.

```bash
python3 scripts/oo2a3.py verify
```

## 보존 경계

- ZIP 파일명·member명·본문·대소문자·수치·상태문을 바꾸지 않는다.
- 03A와 03B를 서로 대체하지 않는다. 03B는 03A 확정 상태의 전달층이다.
- `$rq-sc8-1ab`, `2ab`, `4ab` 등 인접 번호를 자동 호출하거나 결합하지 않는다.
- OO2·OO2A2·OO2B2·NAK·SC3를 자동 결속하지 않는다.
- SC7이나 일반 조티시 지식으로 공백·HOLD를 보충하지 않는다.
- Rashi와 Bhava, House Transfer와 Entity Transfer, forward와 reverse 상태를 합치지 않는다.
- Source 안의 `VOID`, `HOLD`, `N.A.`, `SOURCE_SCOPE_EXCLUDED`, `SUPPORT_ONLY`를 그대로 보존한다.
- 단독 호출에서 해석·사건·시기·귀속·보유·회수 판정을 실행하지 않는다.

Source 동일성이나 구성 검문이 필요할 때만 `references/source-manifest.json`을 읽는다.
