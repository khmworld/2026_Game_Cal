# 2026_Game_Cal

PySide6 기반 게임 일정 캘린더 앱입니다.

## 빌드 의존성

```bash
pip install -r requirements.txt
```

## PyInstaller 빌드 설정

`GameCalendar.spec`는 **one-dir(디렉터리 배포)** 방식을 고정으로 사용합니다.

### 선택 근거

- **시작 속도**: one-dir은 실행 시 임시 폴더로 추가 압축 해제를 하지 않아 one-file 대비 초기 실행 지연이 적습니다.
- **배포 용량/형태**: one-file은 단일 파일로 배포가 편하지만 내부 압축/번들 구조 때문에 실제 배포 크기 관점에서 항상 유리하지 않습니다. 본 프로젝트는 리소스(`ui_style.qss`, `calendar.md`)를 함께 배포하는 성격이라 one-dir이 관리가 직관적입니다.
- **백신 오탐 가능성**: 일반적으로 one-file 단일 실행 파일은 런타임 self-extract 동작 특성 때문에 백신 오탐 가능성이 상대적으로 높게 보고됩니다. one-dir은 이런 패턴이 줄어드는 편입니다.

## 포함 리소스

`GameCalendar.spec`에서 다음 파일을 데이터 파일로 포함합니다.

- `ui_style.qss`
- `calendar.md` (샘플 일정 파일)
