# Odd Realm 한글화 개발툴

Odd Realm 한글패치를 **처음부터 다시 만들어 내는** 도구 모음입니다.
게임이 업데이트되거나 번역을 고치고 싶을 때 여기서 다시 빌드하면 됩니다.

---

## 준비 (처음 한 번만)

1. Python 3.10 이상 설치 — https://www.python.org/downloads/
   설치할 때 **Add Python to PATH** 를 꼭 체크하세요.
2. 명령 프롬프트를 이 폴더에서 열고:

   ```
   pip install -r requirements.txt
   ```

   (numpy, pillow 두 개만 씁니다.)

3. (선택) 단일 exe 설치기도 만들려면 [Go](https://go.dev/dl/) 를 설치하세요.
   없으면 그 단계만 건너뛰고 스크립트판까지는 정상적으로 만들어집니다.

---

## 빌드하기

```
python 1_원본가져오기.py
python 2_빌드.py
```

- **1_원본가져오기.py** — 게임 폴더에서 패치 대상 원본 5개 파일을 `original/` 로 복사합니다.
  이미 한글패치가 깔려 있어도 `_KoreanPatch_Backup` 에서 원본을 찾아옵니다.
  SHA-256 으로 원본이 맞는지 확인하므로, 엉뚱한 파일이 들어갈 일은 없습니다.
- **2_빌드.py** — 아래 5단계를 순서대로 돌립니다. 12초쯤 걸립니다.

  | 단계 | 스크립트 | 하는 일 |
  |---|---|---|
  | 1 | `build_all.py` | 툴팁·대사·튜토리얼 번들 3종을 번역해 다시 패킹 |
  | 2 | `buildko.py` | Galmuri11 한글 아틀라스를 만들어 `resources.assets` 에 주입 |
  | 3 | `metapatch.py` | IL2CPP `global-metadata.dat` 의 UI 문자열 943개 교체 |
  | 4 | `dist_gen/mkdelta.py` | 원본 ↔ 패치본 차분(ORKP1) 생성 |
  | 5 | `dist_gen/mkexe.py` | Go 단일 exe 설치기 빌드 (Go 없으면 자동 생략) |
  | 6 | `dist_gen/mkpackage.py` | 스크립트판 zip 조립 |
  | 7 | `dist_gen/mkdirect.py` | 직접 교체용 zip 조립 (실행 파일 0개) |

결과물은 `out/` 에 생깁니다.

```
out/patch/       번역된 번들 3종
out/resources.assets
out/patch_meta/global-metadata.dat
out/build/patch.orkp      델타 (557KB)
out/dist/                 ← 최종 배포물
  OddRealm_한글패치_vX.X.X.exe              받아서 더블클릭 (주 배포본)
  OddRealm_한글패치_vX.X.X_직접교체용.zip    압축 풀어 덮어쓰기 (실행 파일 0개)
  OddRealm_한글패치_vX.X.X_스크립트판.zip    ps1 우클릭 실행
```

---

## 번역 고치기

번역 데이터는 전부 `tr/` 안에 있습니다. 고치고 `python 2_빌드.py` 만 다시 돌리면 됩니다.

| 위치 | 내용 |
|---|---|
| `tr/glossary*.py` | 낱말 용어집. `Iron → 철` 처럼 토큰 단위 대응 |
| `tr/phrases1~3.py` | 문장 통째로 덮어쓰는 대응표 |
| `tr/rules.py` | 정규식 패턴, 동사 처리 규칙 |
| `tr/josa.py` | 받침에 따른 조사 자동 선택 (을/를, 으로/로) |
| `tr/tx.py` | 위를 조합하는 번역 엔진. 어순 재배치도 여기 |
| `tr/desc/*.json` | 설명문 822개 (수동 번역) |
| `tr/dlg/*.json` | NPC 대사 401개 |
| `tr/tut/*.json` | 튜토리얼 33개 |
| `tr/meta/m1~m3.json` | UI 문자열 943개 (IL2CPP 리터럴) |

### ⚠ `tr/meta/` 를 건드릴 때 반드시 지킬 것

게임 코드의 문자열 리터럴 중 일부는 **UI 라벨이 아니라 데이터 로드 키**입니다.
이걸 번역하면 게임이 해당 데이터를 못 찾아 새 게임 시작 시 무한 로딩에 빠집니다.
(v1.0 에서 실제로 터졌던 문제. `Entities` / `Items` / `Party` / `Notifications` 4개)

**검증 방법** — 패치 후 게임을 한 번 켜고 로그를 확인하세요.

```
%USERPROFILE%\AppData\LocalLow\Unknown Worlds\Odd Realm\Player.log
```

로그에 `Loading <카테고리>` 줄이 93개쯤 찍힙니다. **이 줄에 한글이 하나라도 보이면
그 낱말은 데이터 키입니다. 즉시 `tr/meta/` 에서 빼고 다시 빌드하세요.**

```
Loading blueprints      ← 정상
Loading entityage       ← 정상
Loading 개체            ← 문제! "Entities" 를 번역해서 깨진 것
```

---

## 폰트 바꾸기

`mkfont.py` 의 상수만 만지면 됩니다.

```python
FONT = orpaths.FONT_TTF   # font/Galmuri11.ttf
PPEM = 11                 # 렌더링 픽셀 크기
BEARING_SHIFT = 1         # 글리프를 1px 내려 라틴 베이스라인에 맞춤
```

`buildko.py` 의 `AW/AH` 는 아틀라스 크기(2048×768)이고,
FaceInfo 의 `pointSize 16 / scale 0.7 / ascent 7 / lineHeight 9` 는
**원본 폰트와 똑같이 유지해야** UI 줄 높이가 안 틀어집니다.
다른 폰트를 쓰려면 `font/` 에 ttf 를 넣고 라이선스도 함께 챙기세요.

---

## 폴더 구조

```
orpaths.py            공통 경로 설정. 모든 스크립트가 이걸 import 한다
game_path.txt         게임 폴더 수동 지정 (자동 탐색 실패 시에만)
requirements.txt

unityser.py           UnityFS 번들 + SerializedFile 파서
tt.py                 타입트리 값 읽기/쓰기 (정렬 규칙 포함)
pack.py               번들 재패킹 + 자체 LZ4 압축기
tmpfont.py            TMP_FontAsset 타입트리
tex.py                Texture2D 타입트리
tmpset.py             TMP_Settings 타입트리
commonstr.py          Unity 공용 문자열 테이블

mkfont.py             TTF → 글리프 비트맵
buildko.py            아틀라스 조립 + resources.assets 주입
build_all.py          번들 3종 번역
metapatch.py          global-metadata.dat 문자열 교체
extract.py scan.py scan2.py patchbundle.py    분석용 보조 도구

dist_gen/mkdelta.py     ORKP1 델타 생성기
dist_gen/mkexe.py       exe 설치기 빌드
dist_gen/mkpackage.py   스크립트판 zip 조립
dist_gen/mkdirect.py    직접 교체용 zip 조립
dist_patcher/ps/        배포되는 설치기 원본 (ps1 + 읽어보세요)
dist_patcher/go/        단일 exe 설치기 Go 소스 (mkexe.py 가 빌드)

font/Galmuri11.ttf    OFL 1.1
original/             원본 5개 파일 (1_원본가져오기.py 가 채움)
out/                  빌드 산출물
```

---

## 게임이 업데이트되면

1. `orpaths.py` 의 `SHA` 값 5개를 새 원본 해시로 갱신
2. `original/` 을 비우고 `1_원본가져오기.py` 다시 실행
3. `2_빌드.py`
4. 잔여 영문이 늘었으면 `extract.py` 로 문자열을 다시 뽑아 `tr/` 보강
5. 위의 `Loading` 로그 검증을 **반드시** 다시 수행

번역 데이터는 원문 문자열을 키로 쓰기 때문에, 게임이 문구를 바꾸면
그 항목만 조용히 미번역으로 남습니다. 크래시는 안 나지만 확인은 필요합니다.

---

## 배포기 원리 (요약)

패치된 `resources.assets`(37MB)와 `global-metadata.dat`(7.4MB)를 그대로 뿌리면
게임 원본 데이터를 통째로 재배포하는 꼴이 됩니다. 그래서 설치기가
**사용자 PC의 원본을 읽어 변경분만 적용**하도록 만들었습니다.
배포물에는 번역문과 한글 폰트만 들어가고, 45MB → 532KB 로 줄어듭니다.

ORKP1 델타 형식:

```
"ORKP1\0\0\0" | uint64 원본바디길이 | zlib(바디)

바디: uint32 파일수
  각 파일: uint16 경로길이 | 경로(UTF-8, / 구분)
           32B srcSHA256 | 32B dstSHA256
           uint64 srcSize | uint64 dstSize
           uint32 opsLen  | ops

ops: uint32 개수
  COPY   : 0x01 | uint64 srcOffset | uint32 len
  INSERT : 0x02 | uint32 len | bytes
```

설치기는 exe 가 아니라 PowerShell 스크립트입니다.
서명 없는 exe 는 구글 드라이브·백신이 악성코드로 오탐해 지워버리기 때문입니다.

### 설치기 손볼 때 주의할 점

- `.ps1` 은 **UTF-8 BOM 필수**. Windows PowerShell 5.1 은 BOM 이 없으면 ANSI 로 읽어 한글이 깨집니다.
- **`.bat` 런처를 넣지 마세요.** `bat` 이 `powershell -ExecutionPolicy Bypass` 를 호출하는 형태는
  악성 다운로더의 전형적인 패턴이라 구글 드라이브·백신이 zip 째로 차단합니다 (v1.0.3에서 제거).
  사용자는 `.ps1` 을 우클릭 → [PowerShell에서 실행] 으로 실행합니다.
  굳이 bat 을 다시 넣는다면 내용은 **ASCII 만** 써야 합니다 (`chcp 65001` 적용 전에 파싱되므로).
- `Join-Path` 를 쓰지 마세요. 존재하지 않는 드라이브(E: 등)를 만나면 예외를 던집니다.
  `[System.IO.Path]::Combine` 과 `[System.IO.File]::Exists` 만 씁니다. (v1.0.2 에서 고친 문제)
- `"$n개"` 처럼 변수 뒤에 한글을 붙이면 PowerShell 이 `$n개` 를 변수명으로 읽습니다. `"$($n)개"` 로 쓰세요.
- `switch` 안의 `break`/`continue` 는 바깥 루프가 아니라 switch 에 걸립니다. 메뉴 루프는 `if/elseif` 로.
