# Logging & Monitoring

- 리소스 관측: CPU, 메모리 등 사용량 모니터링
- 애플리케이션 로그 관측: `stdout` / `stderr` 로그 조회

## Resource Monitoring (`kubectl top`)

> 노드, 파드의 현재 리소스 사용량 조회

- 전제 조건

  - 클러스터에 `metrics-server` 가 설치되어 있어야 `kubectl top` 명령을 사용할 수 있음

- 주요 명령어

  ```bash
  # 노드별 CPU, 메모리 사용량
  kubectl top nodes

  # 파드별 CPU, 메모리 사용량 (기본 네임스페이스)
  kubectl top pods

  # 특정 네임스페이스 파드 리소스 사용량
  kubectl top pods -n <namespace>

  # CPU / 메모리 사용량 기준 정렬
  kubectl top pods --sort-by=cpu
  kubectl top nodes --sort-by=memory
  ```

- 활용 목적

  - 특정 파드/노드가 CPU, 메모리를 과도하게 사용하는지 확인
  - HPA 설정값, 리소스 requests/limits 튜닝 시 참고 지표로 활용

## Managing Application Log (`kubectl logs`)

> 파드에서 stdout/stderr로 출력되는 애플리케이션 로그 조회

### 기본 사용법

```bash
# 단일 컨테이너 파드 로그
kubectl logs <pod-name>

# 실시간 스트리밍 모드 (tail -f 느낌)
kubectl logs -f <pod-name>
```

### 자주 사용하는 옵션

```bash
# 이전 컨테이너 인스턴스 로그 (재시작 전 로그 확인)
kubectl logs --previous <pod-name>

# 최근 n줄만 보기
kubectl logs --tail=100 <pod-name>

# 최근 10분간 로그만 보기
kubectl logs --since=10m <pod-name>
```

### 멀티 컨테이너 파드 로그

하나의 파드에 여러 컨테이너가 있을 경우, 반드시 컨테이너 이름을 지정

```bash
kubectl logs <pod-name> -c <container-name>
kubectl logs -f <pod-name> -c <container-name>
```

### 라벨 기반 로그 조회

Deployment, ReplicaSet 등으로 여러 파드가 떠 있는 경우, 라벨 셀렉터로 한 번에 조회할 수 있음

```bash
# app=my-app 라벨을 가진 모든 파드 로그
kubectl logs -l app=my-app

# 실시간 스트리밍
kubectl logs -f -l app=my-app
```

### 이벤트(Event)와의 차이

- `kubectl logs`

  - 애플리케이션이 출력하는 로그 (stdout/stderr)

- `kubectl describe pod <pod-name>`

  - 스케줄링 실패, 이미지 풀 실패(ImagePullBackOff), OOMKill 등 쿠버네티스 이벤트 확인
