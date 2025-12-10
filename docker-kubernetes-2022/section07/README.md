좋습니다. 말씀해 주신 `build: ./` 형태로 사용하는 걸 기준으로 전체를 다시 정리해서 드리겠습니다.

# Utility Container

> 호스트에 Node.js 등을 설치하지 않고, 컨테이너를 CLI 도구처럼 사용하는 패턴

### 왜 사용하는가?

- 로컬 머신에 Node.js, npm 등의 런타을 설치하지 않고도 `npm init`, `npm install` 등을 실행하기 위함
- 프로젝트별로 다른 버전의 도구(Node, npm, pnpm, Gradle 등)를 컨테이너 이미지로 고정해 버전 충돌을 피하기 위함
- 개발 환경을 팀원 간에 동일하게 맞추기 위한 도구 역할

## `docker exec` vs 유틸리티 컨테이너

먼저 유틸리티 컨테이너용 기본 Dockerfile 예시.

```dockerfile
FROM node:14-alpine

WORKDIR /app
```

- `WORKDIR /app`

  - 컨테이너 안에서 기본 작업 디렉터리를 `/app`으로 고정하는 설정

### `docker exec` 방식

- 개념

  - 이미 실행 중인 컨테이너 안에서 명령을 추가로 실행하는 방식

- 예시

  - `docker exec -it <컨테이너> npm init`

- 특징

  - 해당 컨테이너 내부에 패키지, 파일이 생성됨
  - 애플리케이션 컨테이너에 개발용 작업이 섞여 운영, 개발 역할이 섞이는 구조
  - 운영용 컨테이너를 깨끗하게 유지하고 싶다면 지양하는 것이 좋음

### `docker run` + 유틸리티 컨테이너 방식

- 개념

  - Node 런타이 들어있는 컨테이너를 일시적으로 하나 띄워서 CLI를 실행하고 바로 종료하는 방식

- 예시(공식 이미지 직접 사용)

  - `docker run -it node:14-alpine npm init`

- 문제점

  - 프로젝트 디렉터리가 컨테이너 내부에만 존재하면, 컨테이너 종료 시 작업 내용이 함께 사라지는 구조

- 해결책: 로컬 폴더를 컨테이너에 마운트(미러링)

  ```bash
  docker run -it -v <호스트경로>:/app node:14-alpine npm init
  ```

  - `/app`에 생성된 `package.json` 등이 호스트 `<호스트경로>`에 그대로 반영됨
  - 컨테이너는 일회성 작업용, 실제 결과물은 호스트에 남는 구조

## ENTRYPOINT 활용

유틸리티 컨테이너를 npm 전용으로 만들고 싶다면 Dockerfile을 다음과 같이 확장함.

```dockerfile
FROM node:14-alpine

WORKDIR /app

ENTRYPOINT [ "npm" ] # 컨테이너를 실행할 때 항상 npm이 기본 명령으로 실행됨
```

- 이 설정을 사용하면 `docker run <이미지> <인자>` 형태로 실행할 때

  - `<인자>` 부분이 `npm`의 서브 커맨드로 전달되는 구조

- 예시

  - `docker run -it -v <경로>:/app node-util init`

    - 실제 실행: `npm init`

  - `docker run -it -v <경로>:/app node-util install express --save`

    - 실제 실행: `npm install express --save`

→ 이미지를 npm 전용 유틸리티 컨테이너로 만들어서, npm CLI처럼 사용하는 구조

## Docker Compose로 유틸리티 컨테이너 사용

`build: ./` 설정을 사용해, Compose가 Dockerfile을 기준으로 유틸리티 이미지를 자동으로 빌드하도록 구성함.

```yaml
services:
  npm:
    build: ./ # 현재 디렉터리의 Dockerfile로 유틸리티 이미지 빌드
    stdin_open: true # -i 옵션과 동일, 표준 입력 유지
    tty: true # -t 옵션과 동일, TTY 할당
    volumes:
      - ./:/app # 현재 프로젝트 디렉터리를 컨테이너 /app에 마운트
```

### 기본 사용

- `docker compose run npm init`

  - 현재 디렉터리(`./`)가 `/app`으로 마운트된 상태에서 `npm init` 실행
  - 로컬 프로젝트 폴더에 `package.json` 생성됨

- `docker compose run npm install express --save`

  - 컨테이너 안에서 `npm install express --save` 실행
  - `node_modules`, `package-lock.json` 등이 로컬 폴더에 생성됨

- 유틸리티 컨테이너는 일반적으로 `docker compose up`이 아니라
  `docker compose run npm ...` 형태로 단발성 작업 실행용으로 사용하는 패턴

### 컨테이너 자동 제거 (`--rm`)

- `docker compose run`은 기본적으로 컨테이너를 자동 제거하지 않음

  - 여러 번 실행 시 one-off 컨테이너가 계속 쌓이는 구조

- 실행 후 컨테이너를 바로 지우고 싶다면 `--rm` 옵션 사용함

- 예시

  - `docker compose run --rm npm init`
  - `docker compose run --rm npm install express --save`
    → 실행이 끝나면 유틸리티 컨테이너는 삭제되고, 결과물(파일, 디렉터리)만 호스트에 남는 구조

## 정리

- 유틸리티 컨테이너

  - 호스트에 Node.js 등을 설치하지 않고도 `npm` 명령을 실행하기 위한 도구성 컨테이너 패턴
  - Dockerfile에서 `ENTRYPOINT ["npm"]`을 설정해, 이미지를 `npm` 전용 실행 환경으로 사용함
  - `volumes: ./:/app` 바인드 마운트를 통해, 작업 결과를 로컬 프로젝트 디렉터리에 그대로 반영함
  - `docker compose run --rm npm ...` 형태로, 필요한 순간에만 컨테이너를 띄우고 작업 후 바로 정리하는 구조
