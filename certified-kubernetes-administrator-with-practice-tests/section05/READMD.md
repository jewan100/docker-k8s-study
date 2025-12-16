# Application Lifecycle Management

## Deployment Strategy

> 애플리케이션 버전을 어떻게 교체할지에 대한 전략

Deployment는 내부적으로 ReplicaSet을 버전 단위로 관리하면서, 설정된 전략에 따라 Pod를 교체하는 구조

### Recreate 전략

> 기존 버전을 모두 내렸다가 새 버전을 올리는 방식

- 동작 방식

  - 기존 Pod 전부 종료
  - 이후 새 버전 Pod를 한 번에 생성

- 특징

  - 배포 동안 서비스 단절 발생 가능성
  - 롤백은 빠르지만, 업그레이드 구간에 다운타임이 생길 수 있는 구조

- 사용 사례

  - 내부용, 배포 시간 동안 잠깐 내려가도 되는 서비스
  - 데이터 마이그레이션 등 “구버전과 신버전이 동시에 떠 있으면 안 되는” 특수 상황

Deployment 설정 예시

```yaml
spec:
  strategy:
    type: Recreate
```

### RollingUpdate 전략

> 기본 Deployment 전략, Pod를 조금씩 교체하는 방식

- 동작 방식

  - 새 ReplicaSet을 하나 더 생성
  - 구버전 Pod를 일정 비율로 줄이고, 동시에 신버전 Pod를 일정 비율로 늘리는 구조

- 특징

  - 무중단 또는 거의 무중단에 가까운 배포 가능성
  - 트래픽 일부만 새 버전으로 보내면서 이상 여부를 관찰할 수 있는 구조

- 세부 설정 필드

  - `maxUnavailable` 동시에 빠져도 되는 구버전 Pod 개수 또는 비율
  - `maxSurge` 최대 얼마나 더 많이(임시로) 새 버전 Pod를 띄울지 개수 또는 비율

예시

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0 # 항상 모든 Pod를 유지
      maxSurge: 1 # 한 개씩 초과 생성 허용
```

이미지 교체 명령 예시

```bash
# 이미지만 즉시 교체 (Deployment 이름 기준)
kubectl set image deployment/myapp-deployment myapp=nginx:1.25

# 또는 YAML 수정 후 재적용
kubectl apply -f deployment.yaml
```

> 실제로는 `kubectl apply -f` 로 Deployment 스펙을 변경하면, 자동으로 RollingUpdate 전략에 따라 새 ReplicaSet이 생성되고 트래픽이 점진적으로 이동하는 구조

## Rollout & Rollback

> “롤아웃(rollout)” 은 새로운 버전으로 넘어가는 전체 배포 과정, “롤백(rollback)” 은 이전 리비전으로 되돌리는 작업

Deployment는 내부적으로 “리비전(revision)” 이라는 번호로 버전을 관리

- 롤아웃 상태 확인

```bash
kubectl rollout status deployment/myapp-deployment
```

- 히스토리 조회

```bash
kubectl rollout history deployment/myapp-deployment
kubectl rollout history deployment/myapp-deployment --revision=2
```

- 기본 롤백 (직전 리비전으로 복구)

```bash
kubectl rollout undo deployment/myapp-deployment
```

- 특정 리비전으로 롤백

```bash
kubectl rollout undo deployment/myapp-deployment --to-revision=1
```

#### 디버깅 순서 예시

1. `kubectl set image` 또는 `kubectl apply -f` 로 새 버전 배포
2. `kubectl rollout status` 로 배포 진행 상황 확인
3. 에러 발생 시 `kubectl describe pod`, `kubectl logs` 로 원인 파악
4. 필요 시 `kubectl rollout undo` 로 이전 정상 버전으로 즉시 복구

## Commands & Arguments

> 컨테이너가 “무엇을 어떤 인자로 실행할지” 를 제어하는 설정

Docker 기준

- `ENTRYPOINT` 컨테이너가 실행할 기본 명령
- `CMD` 기본 인자 또는 기본 명령

Kubernetes Pod 기준

- `command` Docker의 ENTRYPOINT 를 override 하는 필드
- `args` Docker의 CMD 를 override 하는 필드 또는 `command` 에 전달할 인자 목록

### 기본 이미지 의존 실행

```yaml
containers:
  - name: app
    image: myorg/myapp:1.0.0
    # Dockerfile 내 ENTRYPOINT, CMD 설정 그대로 사용
```

이미지 내부 Dockerfile 예시

```dockerfile
ENTRYPOINT ["java", "-jar", "app.jar"]
CMD ["--spring.profiles.active=prod"]
```

### command / args 로 명시적 설정

```yaml
containers:
  - name: app
    image: myorg/myapp:1.0.0
    command: ["java", "-jar", "app.jar"] # ENTRYPOINT 역할
    args: ["--spring.profiles.active=prod"] # CMD 역할
```

## Env Variables in Kubernetes

쿠버네티스에서 환경 변수를 주입하는 대표 방식

- Pod 스펙에 직접 key-value 정의 방식
- ConfigMap 리소스를 통한 설정값 관리 방식
- Secret 리소스를 통한 민감 정보 관리 방식

### 1. Plain Key Value

Pod 정의 안에서 바로 환경 변수를 지정하는 방식.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
spec:
  containers:
    - name: simple-webapp
      image: simple-webapp:1.0.0
      env:
        - name: APP_ENV
          value: dev
        - name: APP_PORT
          value: "8080"
```

### 2. ConfigMap

> 환경 변수, 설정값을 중앙에서 관리하기 위한 리소스

- 키-값 쌍 기반 설정 저장소 역할
- 환경별 설정 값, 피처 플래그, 외부 API 엔드포인트 관리 용도

#### ConfigMap 생성

리터럴 기반 생성

```bash
kubectl create configmap app-config \
  --from-literal=APP_COLOR=blue \
  --from-literal=APP_ENV=prod
```

파일 기반 생성

```bash
kubectl create configmap app-config \
  --from-file=./config/app.properties
```

YAML 선언 기반 생성

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_COLOR: blue
  APP_ENV: prod
```

#### Pod에 주입

1. envFrom 전체 주입

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp-color
spec:
  containers:
    - name: simple-webapp-color
      image: simple-webapp-color
      ports:
        - containerPort: 8080
      envFrom:
        - configMapRef:
            name: app-config
```

2. env 단일 키 주입

```yaml
env:
  - name: APP_COLOR
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: APP_COLOR
```

3. Volume 마운트

```yaml
volumes:
  - name: app-config-volume
    configMap:
      name: app-config

containers:
  - name: app
    image: simple-webapp
    volumeMounts:
      - name: app-config-volume
        mountPath: /config
```

### 3. Secret

> 비밀번호, 토큰, 인증서 등 민감 정보 저장용 리소스

- base64 인코딩으로 저장되는 키-값 데이터
- 기본적으로 etcd에 평문 형태로 저장되므로 RBAC, etcd 암호화 설정 필요

#### Secret 생성

리터럴 기반 생성

```bash
kubectl create secret generic app-secret \
  --from-literal=DB_HOST=mysql \
  --from-literal=DB_USER=root \
  --from-literal=DB_PASSWORD=root
```

YAML 선언 기반 생성

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
data:
  DB_HOST: bXlzcWw= # "mysql" base64
  DB_USER: cm9vdA== # "root" base64
  DB_PASSWORD: cm9vdA== # "root" base64
```

인코딩, 디코딩 예시

```bash
echo -n 'root' | base64
echo -n 'cm9vdA==' | base64 --decode
```

#### Pod에 주입

1. envFrom 전체 주입

```yaml
envFrom:
  - secretRef:
      name: app-secret
```

2. env 단일 키 주입

```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: app-secret
        key: DB_PASSWORD
```

3. Volume 파일로 주입

```yaml
volumes:
  - name: app-secret-volume
    secret:
      secretName: app-secret

containers:
  - name: app
    image: myorg/myapp
    volumeMounts:
      - name: app-secret-volume
        mountPath: /etc/secrets
        readOnly: true
```

Secret 관련 주의 사항

- Secret 정의 YAML은 Git 저장소에 커밋하지 않는 패턴 권장
- `.gitignore`, `.dockerignore` 로 Secret 파일 디렉터리 동시 제외 패턴 권장
- etcd 암호화는 `EncryptionConfiguration` 기능으로 별도 설정 필요

## Multi Container Pod

> 하나의 Pod에 여러 컨테이너를 함께 배치하는 패턴

공통 특성

- 동일 네트워크 네임스페이스 공유 구조

  - `localhost` 로 상호 통신 가능

- 동일 Volume 공유 구조
- Pod와 동일한 수명주기를 가지는 컨테이너 집합 구조

### Co-located Containers 패턴

서로 밀접하게 묶인 두 컨테이너를 한 Pod에 배치하는 패턴.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-helper
spec:
  containers:
    - name: web-app
      image: web-app:1.0.0
      ports:
        - containerPort: 8080
    - name: helper
      image: helper:1.0.0
```

- 주로 작은 헬퍼 프로세스를 함께 붙일 때 사용하는 패턴

### Init Containers 패턴

> 메인 컨테이너보다 먼저 실행되어야 하는 초기화 작업을 담당하는 컨테이너

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp
  labels:
    name: simple-webapp
spec:
  initContainers:
    - name: db-checker
      image: busybox
      command: ["sh", "-c", "wait-for-db-to-start.sh"]
    - name: api-checker
      image: busybox
      command: ["sh", "-c", "wait-for-another-api.sh"]
  containers:
    - name: web-app
      image: web-app:1.0.0
      ports:
        - containerPort: 8080
```

특징

- initContainers는 순서대로 하나씩 실행되는 구조
- 모든 initContainers가 성공 종료한 이후에만 main 컨테이너 시작
- Docker Compose의 `depends_on` 에 초기화 스크립트 개념이 추가된 느낌

### Sidecar Containers 패턴

> 메인 컨테이너와 함께 상시 실행되며 부가 기능을 담당하는 컨테이너

대표 용도

- 로그 수집, 전달
- 프록시, 메시 라우터
- 파일 동기화, 설정 리로더

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-webapp-with-sidecar
spec:
  volumes:
    - name: logs
      emptyDir: {}
  containers:
    - name: web-app
      image: web-app:1.0.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
      ports:
        - containerPort: 8080
    - name: log-shipper
      image: busybox
      command: ["sh", "-c", "ship-logs.sh"]
      volumeMounts:
        - name: logs
          mountPath: /logs
```

## Auto Scaling

### Horizontal Pod Autoscaling HPA

> Pod 개수를 자동으로 늘리거나 줄이는 기능

수동 스케일

```bash
kubectl scale deployment my-app --replicas=3
```

메트릭 기반 자동 스케일

```bash
kubectl autoscale deployment my-app \
  --cpu-percent=50 \
  --min=1 \
  --max=10

kubectl get hpa
```

리소스 요청 예시

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

- HPA는 보통 `requests.cpu` 기준 사용률을 참고하는 구조라서 requests 설정이 필수

### Vertical Pod Autoscaling VPA

> Pod 하나당 리소스량을 자동으로 조정하는 기능

수동 스케일

```bash
kubectl edit deployment my-app
# spec.template.spec.containers[].resources.requests, limits 수정
```

자동 VPA 컨트롤러를 사용하는 경우

- Pod 리소스 사용량을 관찰한 뒤 requests, limits 값을 추천 또는 자동 수정
- CPU를 자주 초과하는 워크로드, 메모리 사용량이 점진적으로 증가하는 워크로드 튜닝 용도

### Scaling Cluster Infra

> 노드 수를 늘리거나 줄이는 작업

Node 스케일링 관점

- Manual

  - kubeadm 환경에서 `kubeadm join` 으로 노드 추가
  - 클라우드 콘솔에서 Node Group 크기 수동 조정

- Automated

  - Cluster Autoscaler 등 도구로 워크로드에 따라 노드를 자동 증감하는 구조

### Scaling Workloads

> Workload Pod 스케일링과 Infra Node 스케일링을 구분해서 생각하는 구조

- Manual

  - `kubectl scale`
  - `kubectl edit`

- Automated

  - HPA로 Pod 수 자동 조정
  - VPA로 Pod 리소스량 자동 조정
