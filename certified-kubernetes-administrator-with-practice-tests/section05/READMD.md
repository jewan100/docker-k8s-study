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

---

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

---

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
