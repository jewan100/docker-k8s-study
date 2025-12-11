# Kubernetes Setting

> 공식 문서
> [https://kubernetes.io/ko/](https://kubernetes.io/ko/)

## Installation

Minikube
[https://minikube.sigs.k8s.io/docs/start/](https://minikube.sigs.k8s.io/docs/start/)

Hypervisor Driver
[https://minikube.sigs.k8s.io/docs/drivers/](https://minikube.sigs.k8s.io/docs/drivers/)

kubectl
[https://kubernetes.io/docs/tasks/tools/#kubectl](https://kubernetes.io/docs/tasks/tools/#kubectl)

> [!TIP]
> Docker를 드라이버로 사용 설정
> `minikube config set driver docker`

자주 사용하는 기본 명령

- `minikube start` 클러스터 생성 및 시작
- `minikube status` 클러스터 상태 확인
- `minikube dashboard` 웹 대시보드 실행

## Kubernetes 객체 개념

> [!TIP]
> Kubernetes는 “객체(Object)” 단위로 모든 리소스를 관리하는 구조

- Pod 애플리케이션 컨테이너가 실제로 실행되는 최소 단위
- Deployment Pod 집합을 원하는 개수만큼 유지하고 롤링 업데이트, 롤백을 담당하는 컨트롤러
- Service Pod 집합 앞단의 고정 엔드포인트 및 로드 밸런싱 담당 리소스

### Pod 객체

- 하나 이상의 컨테이너를 담는 최소 실행 단위
- 같은 Pod 안의 컨테이너는

  - 동일한 네트워크 네임스페이스 공유 상태
  - 동일한 Volume 공유 상태

- 직접 `kubectl run` 등으로 만들 수 있으나, 보통 Deployment를 통해 생성하는 패턴

자주 사용하는 명령

- `kubectl get pods` Pod 목록 조회 명령
- `kubectl describe pod <이름>` Pod 상세 정보 조회 명령
- `kubectl delete pod <이름>` 특정 Pod 삭제 명령 (Deployment가 있다면 자동 재생성 구조)

### Deployment 객체

> “이 애플리케이션 Pod를 몇 개 유지하고 어떻게 업데이트할지”를 선언하는 컨트롤러 리소스

역할

- 지정한 replica 수만큼 Pod 유지 기능
- 새 버전 이미지에 대한 롤링 업데이트 기능
- 문제가 생겼을 때 이전 버전으로 롤백 기능

예시 (명령형)

```bash
kubectl create deployment first-app --image=jewan100/kub-first-app:1
kubectl get deployments
kubectl get pods
```

- 이미지가 로컬에만 있고 레지스트리에 없으면 `ImagePullBackOff` 오류 상태

  - Docker Hub 등 외부 레지스트리에 push 후 사용 패턴

삭제 예시

```bash
kubectl delete deployment first-app
```

구조 이해

- Deployment 생성 시 내부적으로 ReplicaSet, Pod가 자동 생성되는 구조
- “Pod를 먼저 만들고, 나중에 Deployment가 생기는 것”이 아니라
  Deployment → ReplicaSet → Pod 순으로 리소스가 내려가는 구조

### Service 객체

> Pod 집합을 하나의 네트워크 엔드포인트로 묶는 리소스

문제점

- 각 Pod는 자체 IP를 가지지만

  - 클러스터 내부에서만 접근 가능한 상태
  - 재시작, 재배포 시 IP가 변경되는 특성

- Pod에 직접 붙는 방식으로는 운영 환경에서 사용하기 어려운 구조

Service 역할

- 라벨 셀렉터로 특정 Pod 집합 선택 역할
- 고정된 가상 IP, DNS 이름 제공 기능
- 선택된 Pod로 트래픽 로드 밸런싱 기능

예시 (명령형)

```bash
kubectl expose deployment first-app --type=NodePort --port=8080
kubectl get services
minikube service first-app
```

`type` 요약

- `ClusterIP` 클러스터 내부 전용 엔드포인트
- `NodePort` 각 노드 IP:포트로 외부 접근 엔드포인트
- `LoadBalancer` 클라우드 로드밸런서와 연동되는 외부 엔드포인트 (로컬 환경에서는 동작 방식 차이 존재)

## Scaling

> `kubectl scale deployment/first-app --replicas=3`

- Deployment 기준으로 replicas 수를 늘리면 동일 Pod가 여러 개 생성되는 구조
- `kubectl get pods` 실행 시 3개 Pod 확인 가능
- Service는 이 Pod들로 트래픽을 분산하는 역할
- 특정 Pod에 장애가 발생하면

  - 나머지 Pod가 요청을 처리하는 구조
  - Deployment/ReplicaSet이 자동으로 새 Pod를 생성하는 셀프힐링 구조

## Deployment 업데이트 / 롤백 / 히스토리

### 이미지 업데이트

컨테이너 이름 기준으로 이미지 변경

```bash
kubectl set image deployment/first-app my-node=jewan100/kub-first-app:2
kubectl rollout status deployment/first-app
```

- 일반적으로 새 버전 배포 시 태그를 올려가며 버전 관리하는 패턴

  - 같은 태그를 덮어쓸 수도 있으나, 롤백과 히스토리 추적이 어려운 구조

### 잘못된 이미지 롤백

오류 예시

```text
NAME                         READY   STATUS             RESTARTS   AGE
first-app-5d8b5b8fdd-6t4x9   0/1     ImagePullBackOff   0          24s
first-app-6999587d57-7tjtj   1/1     Running            0          4m35s
```

롤백 명령

```bash
kubectl rollout undo deployment/first-app
```

롤백 후 상태

```text
NAME                         READY   STATUS    RESTARTS   AGE
first-app-6999587d57-7tjtj   1/1     Running   0          5m49s
```

### 히스토리 조회 및 특정 리비전 롤백

```bash
kubectl rollout history deployment/first-app
```

```text
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
```

특정 리비전 상세 조회

```bash
kubectl rollout history deployment/first-app --revision=1
```

특정 리비전으로 롤백

```bash
kubectl rollout undo deployment/first-app --to-revision=1
```

## 명령적(Imperative) 접근 방식 vs 선언적(Declarative) 접근 방식

### 명령적 접근 방식

> `docker run`과 비슷한 느낌의 직접 명령 실행 방식

- `kubectl` 명령을 직접 실행해 리소스를 생성, 수정, 삭제하는 방식
- 예시

  - `kubectl create deployment ...`
  - `kubectl expose deployment ...`
  - `kubectl scale deployment ...`

장점

- 빠른 실험, 학습, 단일 작업에 적합한 방식

단점

- 상태를 사람이 기억해야 하는 특성
- 동일 환경을 여러 번 재현하기 어려운 구조

### 선언적 접근 방식

> `docker compose`를 사용하는 방식과 유사한 설정 기반 방식

- YAML 파일에 “원하는 상태”를 정의하고 `kubectl apply`로 적용하는 방식
- 예시

  - `kubectl apply -f deployment.yaml`
  - `kubectl apply -f service.yaml`

특징

- 변경 사항을 비교해 필요한 부분만 반영하는 동작
- Git에 YAML을 버전 관리함으로써 환경 자체를 코드로 관리하는 IaC 방식에 적합한 구조

## 선언적 Deployment / Service 예시

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment # 생성할 리소스의 종류(타입), 여기서는 Deployment
metadata:
  name: my-app-deployment # Deployment 이름
  labels:
    group: example # Deployment에 부여할 메타데이터 라벨
spec:
  replicas: 1 # 유지할 Pod 개수(레플리카 수)
  selector: # 이 Deployment가 관리할 Pod를 찾는 기준(셀렉터)
    matchLabels:
      app: my-app # 라벨이 app=my-app인 Pod 선택
      tier: backend # 라벨이 tier=backend인 Pod 선택
  template: # selector에 매칭될 Pod 템플릿 정의
    metadata:
      labels:
        app: my-app # 생성되는 Pod에 부여할 라벨
        tier: backend # selector와 일치하도록 tier 라벨도 부여
    spec: # Pod 스펙 정의
      containers: # Pod 안에 포함될 컨테이너 목록
        - name: my-node # 컨테이너 이름
          image: jewan100/kub-first-app:2 # 사용할 컨테이너 이미지
          imagePullPolicy: Always # 항상 레지스트리에서 이미지를 다시 pull
          livenessProbe: # 컨테이너 생존 여부를 주기적으로 체크하는 프로브
            httpGet: # HTTP GET 방식으로 헬스 체크 수행
              path: / # 헬스 체크 요청을 보낼 경로
              port: 8080 # 헬스 체크 요청을 보낼 컨테이너 포트
            periodSeconds: 10 # 헬스 체크 주기(초)
            initialDelaySeconds: 5 # 컨테이너 시작 후 첫 체크까지 대기 시간(초)
          # 선택: 문서화를 위한 containerPort 명시 가능
          # ports:
          #   - containerPort: 8080
```

### Service

```yaml
apiVersion: v1
kind: Service # 생성할 리소스 타입, 여기서는 Service
metadata:
  name: backend # Service 이름 (DNS 이름으로도 사용됨)
spec:
  selector:
    app: my-app # 라벨이 app=my-app인 Pod로 트래픽 전달
  ports:
    - protocol: TCP # 사용할 L4 프로토콜 (기본값은 TCP)
      port: 80 # Service가 노출하는 포트 (클라이언트가 접근하는 포트)
      targetPort: 8080 # 실제 Pod 컨테이너가 리슨하는 포트
  type: LoadBalancer # Service 타입 (ClusterIP, NodePort, LoadBalancer 등)
```

적용 예시

```bash
kubectl apply -f k8s.yaml
```

여기서 `k8s.yaml` 안에 Service와 Deployment를 `---` 구분자로 함께 넣을 수 있는 멀티 문서 구성 가능

## Selector

Deployment, Service 등에서 공통으로 사용하는 “Pod 집합 선택 기준” 개념

- `matchLabels`

  - `key: value` 형태로 완전히 일치하는 라벨을 가진 Pod 선택 방식
  - 예시

    - `app: my-app`
    - `tier: backend`

- `matchExpressions`

  - 보다 유연한 조건식 표현 방식
  - 구성 요소

    - `key` 라벨 키
    - `operator` In, NotIn, Exists, DoesNotExist 등 연산자
    - `values` 값 목록

  - 예시

    - `key: tier, operator: In, values: ["backend", "worker"]` 조건

## Liveness Probe (활성 프로브)

> 컨테이너가 “살아 있는지”를 주기적으로 체크하는 설정

- livenessProbe 실패 시

  - kubelet이 컨테이너를 재시작하는 동작
  - 애플리케이션이 데드락, 무한 루프 등 비정상 상태에 빠졌을 때 자동 복구 목적

예시

```yaml
livenessProbe:
  httpGet:
    path: / # 헬스 체크 요청 경로
    port: 8080 # 헬스 체크 요청 포트
  periodSeconds: 10 # 체크 주기(초)
  initialDelaySeconds: 5 # 컨테이너 시작 후 첫 체크까지 대기 시간(초)
```

자주 함께 사용하는 프로브

- `readinessProbe`

  - 요청을 받아도 되는 상태인지 판단하는 프로브
  - 실패 시 Service 로드 밸런싱 대상에서 제외되는 동작

- `startupProbe`

  - 애플리케이션 초기 구동 시간이 긴 경우, 초기 부팅 완료까지 기다리기 위한 프로브

## kubectl 주요 명령어 요약

조회 명령

- `kubectl get pods`
- `kubectl get deployments`
- `kubectl get services`
- `kubectl get all`

상세 조회 명령

- `kubectl describe pod <이름>`
- `kubectl describe deployment <이름>`

생성 명령 (명령적 방식)

- `kubectl create deployment ...`
- `kubectl expose deployment ...`

수정 명령

- `kubectl set image deployment/<이름> <컨테이너>=<이미지:태그>`
- `kubectl scale deployment/<이름> --replicas=N`

롤링 업데이트 관련 명령

- `kubectl rollout status deployment/<이름>`
- `kubectl rollout history deployment/<이름>`
- `kubectl rollout undo deployment/<이름> [--to-revision=N]`

삭제 명령

- `kubectl delete deployment <이름>`
- `kubectl delete service <이름>`
- `kubectl delete -f k8s.yaml`
