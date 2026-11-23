# Codex GBrain Starter

Codex에서 프로젝트별 결정과 작업 기록을 이어 쓰는 로컬 환경입니다. GBrain은 PostgreSQL에 기록을 저장하고, WebUI에서는 문서 제목과 본문을 검색할 수 있습니다. 기본 구성은 임베딩이나 외부 모델 API 키 없이 실행됩니다.

## 설치

Git, Python 3.8 이상, Docker Compose가 필요합니다. Windows에서는 아래 명령의 `python`을 `py`로 바꿔도 됩니다.

```sh
git clone https://github.com/yooseongc/codex-gbrain-starter.git
cd codex-gbrain-starter
python setup.py
docker compose up -d --build
docker compose exec gbrain gbrain stats
```

설치 스크립트는 고정된 WebUI 소스에 본문 검색 패치를 적용하고 새 설치의 비밀번호를 `.env`에 생성합니다. 브라우저에서 [문서 탐색기](http://127.0.0.1:3100/?display=documents)를 열고 `.env`의 `APP_AUTH_PASSWORD`로 로그인하세요. 첫 설치는 빈 데이터베이스로 시작합니다. 포트 3100을 이미 쓰고 있다면 `.env`에 `WEBUI_PORT=3101`을 추가하고 새 포트로 접속하세요.

## Codex 연결

설치 폴더의 절대 경로를 사용해 MCP 서버를 등록하세요. 아래 예시 경로를 실제 위치로 바꾸면 다른 프로젝트에서도 같은 GBrain을 사용할 수 있습니다.

```sh
codex mcp add gbrain -- docker compose -f "/absolute/path/to/codex-gbrain-starter/compose.yaml" exec -T gbrain gbrain serve
```

[프로젝트 지식 관리 규칙](knowledge-rules.md)을 사용자 홈의 `.codex/AGENTS.md`에 추가하세요. 새 Codex 대화에서 “이 프로젝트의 목표를 GBrain에 기록해 줘”라고 요청한 뒤 문서 탐색기에서 저장한 문장을 검색해 보세요.

## 데이터와 원본 프로젝트

`docker compose stop`으로 중지하고 `docker compose start`로 다시 시작합니다. 기록과 설정은 Docker 볼륨에 저장됩니다. `docker compose down -v`를 실행하면 이 볼륨도 삭제됩니다.

엔진은 [garrytan/gbrain](https://github.com/garrytan/gbrain/tree/a5c1748f213289e11f033aea88f63ea5d2cf3603), UI는 [uaysk/GBrain_WebUI](https://github.com/uaysk/GBrain_WebUI/tree/790a862f5fa1b3b3048bae8d13a993f41bc72d41)를 사용합니다. 엔진 버전은 `Dockerfile`, UI 버전은 `setup.py`, 로컬 변경분은 `webui.patch`에서 확인할 수 있습니다.
