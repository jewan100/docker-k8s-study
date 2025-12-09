# Docker Image & Container

## Image

> `Container`의 블루 프린트

- 실제로 코드와 코드를 실행하는데 필요한 도구를 포함
- 이미지를 기반으로 여러 컨테이너를 만듦
- 모든 설정 명령과 모든 코드가 포함된 공유 가능한 패키지
- 여러 개의 레이어(layer) 로 구성되며, Dockerfile의 각 명령이 하나의 레이어가 됨
- 한 번 빌드되면 읽기 전용(Immutable) 이고, 변경 시에는 새로운 이미지를 생성
  - 스냅샷

## Container

> `Image`의 구체적인 실행 인스턴스

- 같은 이미지를 기반으로 여러 컨테이너를 띄워도, 각각 파일 시스템/프로세스가 서로 독립적
- 보통 하나의 주요 프로세스를 중심으로 동작하며, 그 프로세스가 종료되면 컨테이너도 종료
- 상태를 유지하지 않는 Stateless 컨테이너 여러 개를 띄워 수평 확장(Scale-out) 하는 데 많이 사용

<details>
<summary>Docker 관련 명령어</summary>

> `docker * --help`

## DockerFile

| 명령어        | 역할/의미                                        | 비고 / 예시                                                     |
| ------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| `FROM`        | 베이스 이미지(기초 OS/런타임) 지정               | `FROM eclipse-temurin:21-jdk`                                   |
| `WORKDIR`     | 이후 명령들의 기본 작업 디렉터리 설정            | `WORKDIR /app`                                                  |
| `COPY`        | 호스트의 파일/디렉터리를 이미지 내부로 복사      | `COPY build/libs/app.jar app.jar`                               |
| `ADD`         | `COPY` + 압축해제/URL 다운로드 지원              | 특별한 경우에만 사용 권장                                       |
| `RUN`         | 이미지 빌드 시점에 실행할 쉘 명령                | `RUN apt-get update && apt-get install -y curl`                 |
| `EXPOSE`      | 컨테이너가 리슨하는 포트 정보(메타데이터) 명시   | `EXPOSE 8080`                                                   |
| `CMD`         | 컨테이너 시작 시 기본 실행 명령                  | `CMD ["java", "-jar", "app.jar"]`                               |
| `ENTRYPOINT`  | 컨테이너의 메인 프로세스 정의(잘 안 바뀌는 축)   | `ENTRYPOINT ["java", "-jar", "app.jar"]`                        |
| `ENV`         | 환경 변수 설정                                   | `ENV SPRING_PROFILES_ACTIVE=prod`                               |
| `ARG`         | 빌드 타임 인자 정의 (`docker build --build-arg`) | `ARG JAR_FILE=build/libs/app.jar`                               |
| `USER`        | 이후 명령/프로세스를 실행할 리눅스 사용자 지정   | `USER appuser`                                                  |
| `VOLUME`      | 데이터 영속화/마운트를 위한 볼륨 경로 선언       | `VOLUME ["/data"]`                                              |
| `LABEL`       | 이미지에 메타데이터(키-값 정보) 추가             | `LABEL maintainer="jewan@example.com"`                          |
| `SHELL`       | 기본 쉘 변경                                     | `SHELL ["bash", "-c"]`                                          |
| `HEALTHCHECK` | 헬스 체크 명령 정의                              | `HEALTHCHECK CMD curl -f http://localhost:8080/actuator/health` |

## 이미지 관련 명령어

| 명령어                   | 의미 / 언제 쓰는지                        | 예시                                          |
| ------------------------ | ----------------------------------------- | --------------------------------------------- |
| `docker images`          | 로컬에 있는 이미지 목록                   | `docker images`                               |
| `docker rmi 이미지`      | 이미지 삭제                               | `docker rmi nginx:latest`                     |
| `docker pull 이미지`     | 레지스트리(Docker Hub 등)에서 이미지 받기 | `docker pull nginx:latest`                    |
| `docker build -t 태그 .` | Dockerfile로 이미지 빌드                  | `docker build -t my-app:0.0.1 .`              |
| `docker tag SRC DST`     | 이미지에 새 태그 붙이기                   | `docker tag my-app:0.0.1 my-reg/my-app:0.0.1` |
| `docker push 이미지`     | 이미지 레지스트리에 업로드                | `docker push my-reg/my-app:0.0.1`             |

## 컨테이너 관련 명령어

| 명령어                          | 의미 / 언제 쓰는지                               | 예시                                  |
| ------------------------------- | ------------------------------------------------ | ------------------------------------- |
| `docker run 이미지`             | 이미지를 기반으로 **컨테이너 1개 생성 + 실행**   | `docker run ubuntu:22.04`             |
| `docker run -d ...`             | 백그라운드(detached)로 실행                      | `docker run -d nginx`                 |
| `docker run --name 이름 ...`    | 컨테이너 이름 지정                               | `docker run --name my-nginx nginx`    |
| `docker run --rm ...`           | 컨테이너 종료 시 자동 삭제                       | `docker run --rm ubuntu echo hello`   |
| `docker run -p 호스트:컨테이너` | 포트 바인딩(호스트 포트 ↔ 컨테이너 포트)         | `docker run -p 8080:8080 app-image`   |
| `docker run -v 호스트:컨테이너` | 볼륨/디렉터리 마운트                             | `docker run -v /data:/data app-image` |
| `docker ps`                     | **실행 중인 컨테이너 목록**                      | `docker ps`                           |
| `docker ps -a`                  | 중지된 것 포함 전체 컨테이너 목록                | `docker ps -a`                        |
| `docker stop 컨테이너`          | 컨테이너 **정상 종료(SIGTERM)**                  | `docker stop my-nginx`                |
| `docker kill 컨테이너`          | 강제 종료(SIGKILL)                               | `docker kill my-nginx`                |
| `docker start 컨테이너`         | 중지된 컨테이너 다시 실행                        | `docker start my-nginx`               |
| `docker restart 컨테이너`       | 재시작                                           | `docker restart my-nginx`             |
| `docker rm 컨테이너`            | 컨테이너 삭제                                    | `docker rm my-nginx`                  |
| `docker logs 컨테이너`          | 컨테이너 로그 조회                               | `docker logs my-nginx`                |
| `docker logs -f 컨테이너`       | 로그 실시간 follow                               | `docker logs -f my-nginx`             |
| `docker exec -it 컨테이너 쉘`   | 실행 중 컨테이너 안에 들어가서 명령 실행/쉘 접속 | `docker exec -it my-nginx /bin/bash`  |

</details>

---

## Image Layer

> `Image`는 레이어 기반 아키텍처
> 이미지를 빌드할 때, 변경된 부분의 명령과 그 이후의 모든 명령이 재평가됨

- 레이어 기반 모든 명령 결과를 캐싱
- 이미지를 다시 빌드할 때, 명령을 다시 실행할 필요가 없으면 캐시된 결과 사용

### Layer의 특징

- `FROM`, `RUN`, `COPY`, `ADD` 등 각 Dockerfile 명령이 하나의 레이어가 됨
- 한 번 만들어진 레이어는 읽기 전용(Immutable)
- 여러 이미지가 같은 베이스 이미지/레이어를 공유해서 디스크/네트워크 절약
- 컨테이너는 이미지 레이어 위에 쓰기 가능한 레이어(컨테이너 레이어) 를 하나 더 얹어서 사용

### 캐시와 빌드 속도

- 어떤 레이어에서 캐시가 깨지면, 그 이후 레이어는 전부 다시 빌드

  ```dockerfile
  WORKDIR /app      # 레이어 A

  COPY . /app       # 레이어 B

  RUN npm install   # 레이어 C
  ```

  - `COPY .`에서 소스 코드가 바뀌면 B, C 레이어는 다시 실행되고, 그 이전 A는 캐시 사용

- 빌드 속도를 위해, 변경이 적은 명령을 위로, 자주 바뀌는 명령을 아래로 배치

  ```dockerfile
  WORKDIR /app

  # 의존성 정의 파일만 먼저 복사 (캐시 최대 활용)
  COPY package*.json /app
  RUN npm install

  COPY . /app
  ```

  - OS 패키지 설치, 공통 라이브러리 설치 → 위쪽
  - 애플리케이션 소스 COPY, 빌드 → 아래쪽
