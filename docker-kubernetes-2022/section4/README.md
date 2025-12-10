# Docker Communication & Network

## Docker Communication

### 컨테이너 → 월드 와이드 웹

- 기본 `bridge` 네트워크 사용 시, 컨테이너에서 외부 인터넷(WWW)으로 아웃바운드 통신 가능함
- 별도 설정 없이 `curl`, 외부 API 호출, 외부 DB 접속 등 요청 전송 가능함
- 외부(브라우저, 다른 서버) → 컨테이너로 들어오려면 포트 바인딩 필요함

```bash
# 컨테이너 3000 포트를 호스트 3000 포트에 노출
docker run -d -p 3000:3000 --name myapp myapp-image
```

---

### 컨테이너 → 호스트 머신

> Docker Desktop(macOS / Windows): `host.docker.internal`

- 컨테이너 입장에서 **호스트 머신을 가리키는 가상 호스트명**임
- 로컬 개발 중, 호스트에서 실행 중인 DB, 메시지 브로커 등에 접속할 때 사용함

```js
// 컨테이너 안에서 호스트의 MongoDB(27017)에 접속하는 예시
mongoose.connect(
  "mongodb://host.docker.internal:27017/swfavorites",
  { useNewUrlParser: true },
  (err) => {
    if (err) {
      console.log(err);
    } else {
      app.listen(3000);
    }
  }
);
```

- Linux 환경에서는 `host.docker.internal`이 기본 제공되지 않을 수 있음

  - 필요 시 수동 매핑 활용 가능함

```bash
docker run -d \
  --add-host=host.docker.internal:host-gateway \
  --name myapp myapp-image
```

---

### 컨테이너 → 다른 컨테이너

#### 1) IP 주소로 직접 통신

- `docker container inspect <컨테이너>` 로 `IPAddress` 조회 후 IP 기반 통신 방식
- 단점

  - 컨테이너 재시작 시 IP 변경 가능성 존재함
  - 애플리케이션 코드에 IP를 하드코딩해야 하는 번거로움 존재함

#### 2) Docker Network로 묶어서 이름 기반 통신

- 사용자 정의 네트워크를 생성하고 여러 컨테이너를 같은 네트워크에 연결함
- 같은 네트워크 내부에서는 **컨테이너 이름을 도메인(호스트명)처럼 사용 가능함**
- Docker 내부 DNS가 컨테이너 이름 → IP 주소를 자동으로 해결함

```bash
# 1) 사용자 정의 네트워크 생성
docker network create mynet

# 2) MongoDB 컨테이너를 mynet에 연결
docker run -d --name mongodb --network mynet mongo

# 3) 애플리케이션 컨테이너를 같은 네트워크에 연결
docker run -d --name myapp --network mynet myapp-image
```

```js
// 컨테이너 이름(mongodb)을 호스트명처럼 사용
mongoose.connect(
  "mongodb://mongodb:27017/swfavorites",
  { useNewUrlParser: true },
  (err) => {
    if (err) {
      console.log(err);
    } else {
      app.listen(3000);
    }
  }
);
```

---

## Docker Network

> `docker run --network`, `docker network create` 등을 이용해 컨테이너 간 통신 구조 정의 개념임

- Docker 설치 시 기본 네트워크 자동 생성됨

  - `bridge` : 기본 네트워크, 단일 호스트용 가상 스위치 역할
  - `host` : 컨테이너가 호스트 네트워크를 그대로 공유하는 모드
  - `none` : 네트워크를 완전히 끊은 상태

- 일반적인 개발/운영 환경에서는 **사용자 정의 bridge 네트워크**를 만들어 서비스별로 컨테이너 그룹화함

```bash
# 네트워크 목록 확인
docker network ls

# bridge 드라이버 기반 사용자 정의 네트워크 생성
docker network create mynet

# 특정 네트워크 상세 정보 확인
docker network inspect mynet
```

---

## Docker Network Driver란?

> Docker 네트워크가 **어떤 방식으로 동작할지 결정하는 네트워크 구현 타입(모드)**

- 네트워크 드라이버

  - 컨테이너에 어떤 IP를 줄지,
  - 컨테이너끼리 어떻게 라우팅할지,
  - 외부/호스트와 어떻게 통신할지
    를 정의하는 모듈 개념임

### 주요 네트워크 드라이버

| 드라이버 | 의미                               | 대표 사용 사례                             |
| -------- | ---------------------------------- | ------------------------------------------ |
| bridge   | 단일 호스트 내부 가상 스위치 구조  | 로컬 개발, 단일 서버 컨테이너 통신         |
| host     | 컨테이너가 호스트 네트워크를 공유  | 성능 중요, 포트 매핑 없이 호스트 포트 사용 |
| none     | 네트워크 인터페이스 미할당         | 네트워크가 전혀 필요 없는 배치/작업        |
| overlay  | 여러 호스트에 걸친 가상 네트워크   | Swarm, 오케스트레이션, 분산 환경           |
| macvlan  | 컨테이너에 별도 MAC/IP를 직접 부여 | 컨테이너를 물리 서버처럼 보이게 하는 환경  |

- 단일 서버 기준 가장 많이 사용하는 드라이버

  - 기본: `bridge` 드라이버
  - 특수 상황(성능/디버깅): `host` 드라이버

```bash
# bridge 드라이버 기반 네트워크 명시적 생성 예시
docker network create --driver bridge mynet
```
