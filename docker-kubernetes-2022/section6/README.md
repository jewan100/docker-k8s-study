# Docker Compose

> 여러 컨테이너를 하나의 설정 파일로 정의하고, 한 번에 관리하기 위한 도구

## 왜 등장 ?

- `docker build`, `docker run`, `docker network`, `docker volume` 등을 매번 수동으로 입력하는 번거로움 감소 목적
- 웹 서버, 백엔드, DB 등 여러 컨테이너로 구성된 애플리케이션을 하나의 설정 파일로 선언 관리함
- 하나의 명령으로 모든 컨테이너를 실행, 중지, 재빌드, 로그 확인까지 처리하는 오케스트레이션 도구 역할(단일 호스트 기준)

## 오케스트레이션(Orchestration)과의 관계

- 오케스트레이션
  - 여러 시스템, 애플리케이션, 서비스를 조율·관리해 복잡한 작업을 자동화하는 기술 개념
- Docker Compose
  - 로컬 및 단일 호스트 환경에서 다중 컨테이너 애플리케이션을 정의·관리하는 도구
- Kubernetes, Docker Swarm
  - 여러 노드(서버)에 걸친 분산 환경 오케스트레이션 도구

## Dockerfile과 Docker Compose 관계

- Dockerfile
  - 이미지가 어떻게 만들어지는지 정의하는 빌드 스펙
- Docker Compose
  - 어떤 컨테이너들을 어떤 설정으로 함께 띄울지 정의하는 실행 스펙
- Compose는 Dockerfile을 대체하지 않음
  - `build:` 키로 Dockerfile을 참조하거나
  - `image:` 키로 이미 빌드된 이미지를 사용하는 방식으로 함께 사용함

## Docker Compose 작성

> 기본 설정 파일: `docker-compose.yml` 또는 `compose.yaml`

- 도커 단일 명령어로 하던 작업을 YAML 설정으로 선언 관리함
- 주요 항목
  - `services` : 실행할 컨테이너(서비스) 정의
  - `build` : Dockerfile 경로, 빌드 컨텍스트 정의
  - `image` : 사용할 이미지 이름·태그 지정
  - `ports` : 호스트 포트 ↔ 컨테이너 포트 매핑 설정
  - `volumes` : Volume, Bind Mount 설정
  - `env_file`, `environment` : 환경 변수 설정
  - `depends_on` : 서비스 간 의존 관계 정의
  - `networks` : 사용자 정의 네트워크 지정

## Docker Compose와 네트워크

- `docker compose up` 실행 시 프로젝트 전용 기본 네트워크 자동 생성됨
  - 네트워크 이름 예시: `<프로젝트명>_default`
- `services`에 정의된 모든 컨테이너는 기본적으로 같은 네트워크에 자동 연결됨
- 같은 Compose 프로젝트 내에서는 서비스 이름을 호스트명처럼 사용 가능함
  - 예: `backend` 컨테이너에서 `mongodb:27017` 으로 접속 가능함
- 필요 시 `networks` 섹션을 정의해 별도의 네트워크를 명시적으로 구성 가능함

## Docker Compose 기본 명령어

- `docker compose up`
  - Compose 파일 내용을 기준으로 컨테이너 생성 및 실행
- `docker compose up -d`
  - 백그라운드(detached) 모드 실행
- `docker compose down`
  - `up`으로 생성한 컨테이너, 네트워크 등을 정리
  - 기본 설정에서는 named volume은 유지
- `docker compose build`
  - `build:` 설정을 기준으로 이미지 빌드만 수행, 컨테이너는 실행하지 않음
- 자주 사용하는 추가 명령
  - `docker compose ps` : 현재 프로젝트 컨테이너 목록 조회
  - `docker compose logs` : 전체 또는 특정 서비스 로그 조회
  - `docker compose restart` : 서비스 재시작
  - `docker compose stop` : 컨테이너 정지(리소스 유지)
  - `docker compose rm` : 정지된 컨테이너 제거
