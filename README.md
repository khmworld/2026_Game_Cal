# 게임 캘린더 (PySide6)

Windows에서 실행되는 오프라인 게임 일정 캘린더 앱입니다.  
동일 폴더의 `calendar.md`를 파싱해 월간 캘린더 + 우측 일정 카드로 표시합니다.

## 주요 기능
- 월간 캘린더 뷰(일~토) + 우측 일정 카드 패널
- 날짜 클릭 필터링
- 검색(`Ctrl+F`): 제목/태그/플랫폼/장르/상태
- 상태/플랫폼/장르 필터
- URL 시각화
  - 캘린더 셀: 링크 포함 일정 `🔗` 표시
  - 우측 카드: 도메인 라벨 + 링크 열기 버튼
- 다크/라이트 모드 전환
- 내보내기
  - 월 캘린더 PNG 저장
  - 전체 일정 CSV 저장(UTF-8 BOM)

## 프로젝트 구조
- `app.py`: 앱 엔트리, 리소스 로딩, 락 파일 처리
- `parser.py`: `calendar.md` 파싱(표 + 목록 포맷 지원)
- `models.py`: 이벤트 모델/상태 타입
- `ui_main.py`: 메인 UI
- `ui_style.qss`: 스타일
- `export.py`: CSV/PNG 내보내기
- `GameCalendar.spec`: PyInstaller 빌드 설정

## calendar.md 입력 형식
앱은 **표 포맷**과 **기존 목록 포맷**을 모두 지원합니다.

### 1) 표 포맷 (권장)
```md
## 2월 (February 2026)
| 날짜(또는 범위) | 구분 | 이모지 | 한글명 | 플랫폼 | 장르 | URL |
|---|---|---|---|---|---|---|
| 2026-02-23 ~ 2026-03-02 | **[확정]** | 🧪 | 스팀 넥스트 페스트 2월 | PC | 행사 | https://store.steampowered.com/sale/nextfest |
| 2026-02-11 09:00 PT | **[확정]** | 🪜 | 디아블로 II 래더 시즌 종료 | PC/PS/Xbox/Switch | 시즌 | https://example.com |
| 2026-02 (말) | **[예상]** | 🔥 | 디아블로 IV 시즌 진행 | PC/PS5/PS4/XSX\|S/XBO | 시즌 | https://diablo4.blizzard.com/season |
```

지원 날짜 규칙:
- `YYYY-MM-DD`
- `YYYY-MM-DD ~ YYYY-MM-DD`
- `YYYY-MM-DD HH:MM TZ` (시간은 설명 메타로 보존)
- `YYYY-MM (초|중|말)` / `YYYY-MM`

주의:
- `XSX|S`처럼 `|`가 필요한 텍스트는 `XSX\|S`로 이스케이프하세요.
- 상태는 `[확정]`, `[공식]`, `[예상]`, `[확실하지 않음]` 권장.

### 2) 목록 포맷 (하위 호환)
```md
## 2월 2026
- 2026-02-20 🔁 Diablo II 시즌 시작 [확정] (https://example.com)
- 2026-02-23 ~ 2026-03-02 [확정] Steam Next Fest
- 2026-02 [예상] 대형 시즌 업데이트
```

## ChatGPT로 표 생성하기
아래 프롬프트를 ChatGPT에 입력하면 `calendar.md`용 표를 생성할 수 있습니다.

```text
당신은 게임 일정 편집자입니다.
아래 규칙으로 Markdown 표를 생성하세요.
- 월 헤더: ## 2월 (February 2026)
- 표 컬럼: 날짜(또는 범위) | 구분 | 이모지 | 한글명 | 플랫폼 | 장르 | URL
- 상태는 **[확정]** 또는 **[예상]** 사용
- 날짜 형식: YYYY-MM-DD, YYYY-MM-DD ~ YYYY-MM-DD, YYYY-MM (초/중/말)
- 플랫폼 예시: PC/PS5/PS4/XSX\|S/XBO
- 출력은 Markdown만, 불필요한 설명 금지
- 각 행 URL은 실제 https 링크 사용
```

생성 예시:
```md
## 3월 (March 2026)
| 날짜(또는 범위) | 구분 | 이모지 | 한글명 | 플랫폼 | 장르 | URL |
|---|---|---|---|---|---|---|
| 2026-03-19 ~ 2026-03-26 | **[확정]** | 🛍️ | 스팀 봄 세일 2026 | PC | 행사 | https://store.steampowered.com |
| 2026-03-10 | **[확정]** | 🔥 | 디아블로 IV 시즌 12 시작 | PC/PS5/PS4/XSX\|S/XBO | 시즌 | https://diablo4.blizzard.com/season |
| 2026-03 (중) | **[예상]** | ⚙️ | 패스 오브 엑자일 2 리그 체크포인트 | PC/PS5/XSX\|S | 시즌 | https://www.pathofexile.com |
```

## 로컬 실행
```powershell
python app.py
```

## calendar.md 변경 방법 (실전 절차)
개발 중에는 루트 `calendar.md`를 기준본으로 수정하세요.

1. 루트 파일 수정: `.\calendar.md`
2. 문법 빠른 확인(권장): `python app.py` 실행 후 일정이 정상 표시되는지 확인
3. 배포 폴더 동기화(필요 시):
```powershell
copy .\calendar.md .\dist\GameCalendar_onedir\calendar.md /Y
```
4. 재빌드 시에는 `build.ps1`이 자동으로 최신 `calendar.md`를 배포 폴더로 복사합니다.

주의:
- 표에서 열 구분 `|` 문자를 데이터로 써야 하면 `\|`로 이스케이프하세요. 예: `XSX\|S`
- URL이 비어 있으면 링크 버튼/도메인 표시가 나오지 않습니다.

## 빌드 방법 (one-dir)
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m PyInstaller GameCalendar.spec --clean -y
```

빌드 결과:
- `dist\GameCalendar_onedir\GameCalendar_onedir.exe`
- `dist\GameCalendar_onedir\calendar.md`
- `dist\GameCalendar_onedir\assets\app_icon.png`
- `dist\GameCalendar_onedir\assets\app_icon.ico`

## 빌드 없이 사용하기 (배포 ZIP)
빌드 환경이 없는 사용자는 아래 ZIP만 받아서 바로 실행할 수 있습니다.

- 배포 파일: `GameCalendar_onedir.zip`
- ZIP 내부 폴더: `GameCalendar_onedir`

사용 방법:
1. `GameCalendar_onedir.zip`을 원하는 위치에 압축 해제합니다.
2. 압축 해제된 폴더에서 `GameCalendar_onedir.exe`를 실행합니다.
3. 같은 폴더의 `calendar.md`를 수정하면 앱 내용이 바로 반영됩니다.

주의:
- `GameCalendar_onedir.exe`와 `calendar.md`는 같은 폴더에 있어야 합니다.
- 아이콘/스타일 리소스가 필요하므로 `assets` 및 `_internal` 폴더를 함께 유지해야 합니다.
- 첫 실행 시 보안 경고가 뜨면 `추가 정보` → `실행`으로 진행하세요(Windows SmartScreen 환경).

## 실행/배포 시 참고
- 앱은 기본적으로 실행 파일과 같은 폴더의 `calendar.md`를 읽습니다.
- `calendar.md`가 없으면 샘플 파일을 자동 생성합니다.
- 다중 실행은 `gamecalendar.lock`으로 방지합니다.
