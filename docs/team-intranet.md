# 사내망에서 LibreChat과 Oh My Pi로 GBrain 공유하기

팀 서버에 GBrain과 PostgreSQL을 한 번 설치합니다. LibreChat 서버와 각 팀원의 Oh My Pi는 같은 HTTPS 주소로 MCP 요청을 보내고, GBrain은 요청에 담긴 개인별 토큰으로 권한을 확인합니다. 팀원 PC에는 Docker가 필요하지 않습니다.

이 예시는 **팀 전용 신규 설치**, 서버 호스트에서 동작하는 HTTPS 리버스 프록시, 사내 DNS 이름 `brain.corp.example`을 가정합니다. 예시 호스트명과 사용자 이름은 실제 값으로 바꾸세요.

## 1. 서버에서 원격 MCP 시작

서버에 저장소를 복제한 뒤 저장소 루트에서 `python setup.py`를 실행합니다. 생성된 `.env`에 다음 한 줄을 추가하고, 아래 내용을 같은 폴더의 `compose.override.yaml`로 저장하세요. Compose가 기본 파일과 자동으로 병합합니다.

```dotenv
GBRAIN_PUBLIC_URL=https://brain.corp.example
```

```yaml
services:
  gbrain:
    ports:
      - "127.0.0.1:3131:3131"
    environment:
      GBRAIN_PUBLIC_URL: ${GBRAIN_PUBLIC_URL:?Set GBRAIN_PUBLIC_URL in .env}
    command:
      - sh
      - -ec
      - |
        if [ ! -s /root/.gbrain/config.json ]; then
          gbrain init --url "$$GBRAIN_DATABASE_URL" --no-embedding
        fi
        exec gbrain serve --http --bind 0.0.0.0 --port 3131 --public-url "$$GBRAIN_PUBLIC_URL"
```

```sh
docker compose config --quiet
docker compose up -d --build
docker compose exec gbrain gbrain stats
```

사내 DNS에서 호스트명을 프록시의 내부 주소로 연결합니다. 프록시에는 사내에서 신뢰하는 인증서를 설치하고, 사내망에서 들어오는 HTTPS `/mcp` 요청만 `http://127.0.0.1:3131/mcp`로 전달하세요. 요청의 `Authorization` 및 MCP 세션 헤더를 전달하고 스트리밍 응답의 버퍼링을 끕니다. PostgreSQL과 관리자 경로는 서버 내부에 둡니다. 기본 WebUI의 3100번 포트는 브라우저용입니다. [GBrain HTTP 배포 문서](https://github.com/garrytan/gbrain/blob/a5c1748f213289e11f033aea88f63ea5d2cf3603/docs/mcp/DEPLOY.md)

## 2. 관리자가 팀원별 토큰 발급

아래 예시에서 Alice는 LibreChat으로 기록을 작성하고 Bob은 Oh My Pi로 조회합니다. 두 사람을 같은 그룹에 등록한 뒤 각 토큰에 사용자, 자료 공간(`default`), 작업 권한을 명시합니다. 같은 사람이 양쪽 앱을 쓰면 그 사용자 ID로 앱별 토큰을 추가 발급할 수 있습니다.

```sh
docker compose exec gbrain gbrain access member add alice --groups team
docker compose exec gbrain gbrain access member add bob --groups team
docker compose exec gbrain gbrain auth create alice-librechat --member alice --sources default --scopes read,write
docker compose exec gbrain gbrain auth create bob-omp --member bob --sources default --scopes read
```

발급된 값을 각 사용자에게 사내 비밀 전달 수단으로 전달하세요. 팀 공유 문서의 YAML frontmatter에는 아래처럼 독자를 지정합니다. `default`에 사용자 자격으로 새 문서를 작성하면 기본적으로 작성자만 읽을 수 있습니다. [GBrain 팀 자료 접근 모델](https://github.com/garrytan/gbrain/blob/a5c1748f213289e11f033aea88f63ea5d2cf3603/docs/tutorials/company-brain.md)

```yaml
---
title: 팀 연결 테스트
readable_by: [alice, "group:team"]
---
```

토큰을 회수하려면 서버에서 `docker compose exec gbrain gbrain auth revoke bob-omp`처럼 해당 토큰 이름을 지정합니다.

## 3. LibreChat 연결

관리자는 아래 항목을 기존 `librechat.yaml`의 같은 이름 섹션에 병합합니다. `allowedAddresses`에는 호스트와 포트를, `url`에는 전체 HTTPS 주소를 적습니다. 이미 `allowedDomains` 허용 목록을 운영한다면 그 목록에 GBrain 호스트를 추가하세요. 공식 문서는 개발 버전 기준이므로 설치한 LibreChat 버전이 해당 설정을 지원하는지 확인하세요. [내부 주소 허용 설정](https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/mcp_settings) · [MCP 서버 설정](https://www.librechat.ai/docs/configuration/librechat_yaml/object_structure/mcp_servers)

```yaml
mcpSettings:
  allowedAddresses:
    - "brain.corp.example:443"

mcpServers:
  gbrain-team:
    type: streamable-http
    url: "https://brain.corp.example/mcp"
    startup: false
    requiresOAuth: false
    headers:
      Authorization: "Bearer {{GBRAIN_TOKEN}}"
    customUserVars:
      GBRAIN_TOKEN:
        title: "개인 GBrain 토큰"
        description: "관리자가 발급한 본인 토큰을 입력하세요."
```

LibreChat 서버에 설정을 반영하고 재시작합니다. 사용자는 채팅 도구 메뉴에서 `gbrain-team`을 선택하고 개인 토큰을 입력합니다. 주소 차단 또는 인증서 오류가 발생하면 **LibreChat 컨테이너 안에서** 사내 DNS, 허용 목록, 사내 CA 신뢰 설정을 확인하세요.

## 4. Oh My Pi 연결

팀원 PC의 `~/.omp/agent/mcp.json`에 아래 서버를 추가합니다. Oh My Pi를 시작하는 환경에 개인 토큰을 `GBRAIN_TEAM_TOKEN`으로 설정하고 새 세션의 `/mcp`에서 연결 상태를 확인합니다. LibreChat의 이중 중괄호와 Oh My Pi의 환경 변수 표기법이 다릅니다. [Oh My Pi MCP 설정](https://github.com/can1357/oh-my-pi/blob/main/docs/mcp-config.md)

```json
{
  "mcpServers": {
    "gbrain-team": {
      "type": "http",
      "url": "https://brain.corp.example/mcp",
      "headers": { "Authorization": "Bearer ${GBRAIN_TEAM_TOKEN}" }
    }
  }
}
```

프로젝트별 기록 규칙은 [knowledge-rules.md](../knowledge-rules.md)를 참고하세요. 팀 에이전트 지침에 기록 대상 서버 이름과 공유할 문서의 독자 그룹을 함께 적어 두면 개인용 GBrain도 사용하는 팀원이 저장 위치를 구분할 수 있습니다.

## 5. 두 계정으로 공유 범위 확인

1. Alice가 LibreChat에서 “gbrain-team에 `team/connection-test` 페이지를 만들고 본문에 ‘사내 연결 확인’을 저장해 줘. frontmatter의 `readable_by`는 `[alice, "group:team"]`으로 지정해 줘”라고 요청합니다.
2. Bob이 Oh My Pi에서 “gbrain-team으로 `team/connection-test`를 읽어 줘”라고 요청해 같은 문장을 확인합니다.
3. Bob이 그 테스트 문서의 수정을 요청합니다. 읽기 전용 토큰이면 쓰기 도구가 제공되지 않거나 서버가 요청을 거부해야 합니다. Alice가 다시 읽어 원문이 유지됐는지 확인합니다.

연결은 성공했는데 문서가 보이지 않으면 토큰의 자료 공간, 페이지의 `readable_by`, 사용자의 그룹을 확인하세요. 이 절차가 사내 배포의 인수 테스트입니다. 실제 사내 DNS·인증서와 운영 중인 LibreChat 버전에서의 결과는 배포 환경에서 확인해야 합니다.
