# Kubernetes Network(Pod)

## Pod Internal Communication

같은 Pod 안의 컨테이너는 같은 네트워크 네임스페이스를 공유

- 동일 Pod 내 컨테이너 간 통신 주소: `localhost` 또는 `127.0.0.1` 사용 가능
- 동일 Pod 내에서 포트만 다르게 열어 여러 컨테이너를 붙이는 패턴 사용 가능
- 주 사용 사례: 사이드카 패턴, 로그 수집 컨테이너, 프록시 컨테이너 등 역할 분리 구조

반대로

- 다른 Pod에 있는 컨테이너와는 `localhost`로 절대 통신 불가
- 다른 Pod로 통신하려면 Pod IP 또는 Service를 통해 접근 필요

즉, `localhost`는 “같은 Pod 안 컨테이너 간 통신 전용 주소”라는 점 정리 필요

## Pod to Pod Communication (Cluster-Internal)

Kubernetes 클러스터에서는

- 각 Pod마다 고유한 Pod IP 할당 구조
- CNI 플러그인에 의해 노드 간 라우팅이 설정되기 때문에 모든 Pod가 서로 통신 가능한 평면 네트워크 구조
- 기본적으로 네트워크 정책(NetworkPolicy)을 따로 추가하지 않으면 클러스터 내부에서 Pod 간 통신 허용 상태

하지만 코드에서 직접 Pod IP를 쓰는 것은 비권장

- Pod 재시작, 스케일링, 롤링 업데이트 시 Pod IP 변경 가능성
- 여러 인스턴스를 띄웠을 때 로드밸런싱이 자동으로 되지 않는 한계

그래서 등장하는 개념이 Service(특히 ClusterIP)

### ClusterIP Service (내부용 Service)

`auth-service.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: auth-service
spec:
  selector:
    app: auth
  type: ClusterIP # 클러스터 내부에서만 접근 가능한 Service 타입
  ports:
    - protocol: TCP
      port: 80 # Service 포트
      targetPort: 80 # auth 컨테이너 포트
```

특징

- `type: ClusterIP`

  - 클러스터 내부 Pod에서만 접근 가능한 가상 IP 제공 구조
  - 외부(인터넷, 로컬 PC)에서는 직접 접근 불가

- `selector`

  - `app=auth` 라벨을 가진 Pod들을 하나의 백엔드 풀로 묶는 역할

- Service가 가지는 IP를 ClusterIP라고 부름

예시

```bash
kubectl get service

NAME            TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
auth-service    ClusterIP      10.109.214.64    <none>        80/TCP           2m4s
kubernetes      ClusterIP      10.96.0.1        <none>        443/TCP          40h
users-service   LoadBalancer   10.109.194.160   <pending>     8080:31344/TCP   17h
```

- `auth-service`의 ClusterIP: `10.109.214.64`
- 클러스터 내부 Pod에서 `http://10.109.214.64:80` 으로 접근 가능

하지만

- 이 IP도 클러스터 환경에 따라 바뀔 수 있고
- 사람이 직접 하드코딩해서 쓰기에는 유지보수성이 떨어지는 구조

그래서 CoreDNS + Service 이름을 사용하는 것이 정석 구조

## CoreDNS

CoreDNS는 Kubernetes 클러스터 내부의 DNS 서버 역할을 담당하는 컴포넌트

역할

- Service 이름 → ClusterIP로 변환하는 DNS 서버 역할
- Pod 이름 → Pod IP로 변환하는 기능 제공
- FQDN 패턴: `<service>.<namespace>.svc.cluster.local` 구조

예시: `auth-service`

- Service 이름: `auth-service`
- 네임스페이스: `default` 라고 가정
- FQDN: `auth-service.default.svc.cluster.local`
- 일반적으로 다음과 같이 축약 사용 가능

  - `auth-service`
  - `auth-service.default`

실제 코드에서 사용하는 예시

`tasks-deployment.yaml`

```yaml
env:
  - name: AUTH_ADDRESS
    value: auth-service.default # Service DNS 이름 (CoreDNS가 ClusterIP로 변환)
```

`users-deployment.yaml`

```yaml
env:
  - name: AUTH_ADDRESS
    value: auth-service.default # 동일한 방식으로 auth-service 접근
```

이렇게 설정하면

- `tasks` Pod, `users` Pod에서 `AUTH_ADDRESS` 환경 변수를 사용해
  `http://auth-service.default` 형태로 요청 보내기 가능
- CoreDNS가 이를 `auth-service`의 ClusterIP로 자동 변환 처리

## 하드코딩 vs ClusterIP vs CoreDNS

같은 auth 서비스에 접근하는 여러 방식 비교

### 1) Pod IP 하드코딩

예시

- `value: 10.244.1.23` 같은 Pod IP 직접 사용 가정

장점

- 단기 테스트에는 동작 가능

단점

- Pod 재시작, 스케일링, 롤링 업데이트 때 IP 변경 가능성
- 로드밸런싱 없음
- 코드 수정 없이 구조 변경이 사실상 불가능한 구조

결론

- 실서비스, 학습용 정리 기준 둘 다 비권장 방식

### 2) ClusterIP(환경 변수) 하드코딩

Kubernetes는 Service에 대해 자동 환경 변수를 주입

- 예: `auth-service` 의 경우

  - `AUTH_SERVICE_SERVICE_HOST=10.109.214.64`
  - `AUTH_SERVICE_SERVICE_PORT=80`

코드에서

- `AUTH_ADDRESS=10.109.214.64` 같은 값을 직접 하드코딩하는 방식은

  - “사람이 자동 주입값을 보고 그대로 옮겨 적는” 형태라서
  - ClusterIP가 바뀌면 결국 다시 수정해야 하는 구조

장점

- Pod IP 직접 하드코딩보다는 낫지만
- Service DNS를 쓰는 것보다 유지보수성이 떨어지는 구조

### 3) CoreDNS 기반 Service DNS 사용 (권장)

예시

```yaml
env:
  - name: AUTH_ADDRESS
    value: auth-service.default
```

특징

- Service 이름과 네임스페이스만 알고 있으면 됨
- CoreDNS가 내부적으로 `auth-service.default` → ClusterIP로 자동 변환
- ClusterIP가 바뀌어도 Service 이름이 유지되는 한 애플리케이션 코드 수정 불필요 구조
- 스케일 아웃, 롤링 업데이트, 재배포 등 환경 변화에 로버스트한 구조

### 정리 비교

| 방식                      | 설명                                     | 장점                           | 단점                          |
| ------------------------- | ---------------------------------------- | ------------------------------ | ----------------------------- |
| Pod IP 하드코딩           | Pod IP를 코드나 ENV에 직접 입력하는 방식 | 단기 테스트에 활용 가능        | Pod 교체 시 즉시 깨지는 구조  |
| ClusterIP 하드코딩        | Service ClusterIP를 직접 입력하는 방식   | Pod IP보다는 안정적인 구조     | ClusterIP 변경 시 깨지는 구조 |
| Service DNS(CoreDNS) 사용 | `<service>.<namespace>` 형태 이름 사용   | 구성 변경에도 그대로 동작 구조 | DNS 의존성에 대한 이해 필요   |
