# Logging & Monitoring

- 리소스 관측: CPU, 메모리 등 사용량 모니터링
- 애플리케이션 로그 관측: `stdout` / `stderr` 로그 조회

## Resource Monitoring (`kubectl top`)

> 노드, 파드의 현재 리소스 사용량 조회

- 전제 조건

  - 클러스터에 `metrics-server` 가 설치되어 있어야 `kubectl top` 사용 가능

- 주요 명령어

  ```bash
  # 노드별 CPU, 메모리 사용량
  kubectl top nodes

  # 파드별 CPU, 메모리 사용량 (기본 네임스페이스)
  kubectl top pods

  # 특정 네임스페이스 파드 리소스 사용량
  kubectl top pods -n <namespace>

  # CPU 사용량 기준 정렬
  kubectl top pods --sort-by=cpu
  kubectl top nodes --sort-by=memory
  ```
