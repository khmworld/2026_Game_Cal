# 게임 캘린더 (PySide6)

Windows에서 실행되는 오프라인 게임 일정 캘린더 앱입니다.  
동일 폴더의 `calendar.md`를 파싱해 월간 캘린더 + 우측 일정 카드로 표시합니다.

## 주요 기능
- 월간 캘린더 뷰(일~토) + 우측 일정 카드 패널
- 날짜 클릭 필터링
- 검색(`Ctrl+F`): 제목/태그/플랫폼/장르/상태
- 상태/플랫폼/장르 필터
- 다크/라이트 모드 전환
- 내보내기
  - 월 캘린더 PNG 저장
  - 전체 일정 CSV 저장(UTF-8 BOM)

## 프로젝트 구조
- `app.py`: 앱 엔트리, 리소스 로딩, 락 파일 처리
- `parser.py`: `calendar.md` 파싱
- `models.py`: 이벤트 모델/상태 타입
- `ui_main.py`: 메인 UI
- `ui_style.qss`: 스타일
- `export.py`: CSV/PNG 내보내기
- `GameCalendar.spec`: PyInstaller 빌드 설정

## calendar.md 입력 형식
아래 형태를 기본으로 지원합니다.

```md
## 2월 2026
- 2026-02-20 🔁 Diablo II 시즌 시작 [확정] (https://example.com)
- 2026-02-23 ~ 2026-03-02 [확정] Steam Next Fest
- 2026-02 [예상] 대형 시즌 업데이트
```

지원 규칙:
- 월 헤더: `## 2월 2026`, `## 2026-02`, `## 2026년 2월`, `## 2월 (February 2026)`
- 날짜: `YYYY-MM-DD`, `YYYY-MM-DD ~ YYYY-MM-DD`, `YYYY-MM`(월 단위 예상)
- 상태: `[확정]`, `[공식]`, `[예상]`, `[확실하지 않음]`
- 설명: `—` 또는 `-` 뒤 텍스트(장르 추출에 사용)
- URL: `(https://...)` 또는 본문 URL

## 로컬 실행
```powershell
python app.py
```

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
