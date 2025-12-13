# Kubernetes Core

## Control Plane 구성요소

### ETCD

> 분산 환경에서 신뢰성 있게 동작하는 키-값 저장소

- 클러스터 전체 상태를 저장하는 데이터베이스 역할

  - 노드 목록, Pod 스펙, Service, ConfigMap, Secret, Deployment 등 상태 정보 저장

- `kubectl get`으로 보는 모든 객체 정보의 최종 소스는 etcd 저장소
- `kube-apiserver`만 etcd와 직접 통신하는 구조
- 명령어 도구 `etcdctl`로 직접 조회 및 관리 가능

### kube-apiserver

> Kubernetes API 엔드포인트 역할

- 모든 요청 진입점

  - `kubectl` 명령, Dashboard, 다른 컴포넌트 요청의 종착지

- 인증, 인가, Admission Webhook 등을 거친 후 etcd에 읽기, 쓰기 수행
- Control Plane의 “프론트 도어” 역할

### kube-controller-manager

> 클러스터 상태를 원하는 목표 상태로 맞추는 컨트롤 루프 집합

- 여러 컨트롤러 프로세스를 하나의 바이너리로 묶은 컴포넌트

  - Node Controller
  - ReplicaSet Controller
  - Deployment Controller
  - Job / CronJob Controller 등

- 역할

  - 실제 상태와 원하는 상태의 차이를 계속 비교하고 수정하는 “조정자(Reconciler)” 역할
  - 예: ReplicaSet에 replicas=3인데 실제 Pod가 2개면 Pod 1개 추가 생성

### kube-scheduler

> 생성된 Pod를 어느 노드에 배치할지 결정하는 스케줄러

- Pending 상태의 Pod들 중

  - CPU, 메모리 요청량
  - 노드 라벨, taint/toleration
  - NodeAffinity, PodAffinity, AntiAffinity
    등을 고려해 가장 적합한 노드를 선택하는 역할

- 선택 결과를 API Server에 기록하고, 이후 kubelet이 해당 노드에서 Pod 실제 실행

## Node 구성요소

### kubelet

> 각 워커 노드에서 Pod를 실제로 실행, 관리하는 에이전트

- 각 노드마다 동작하는 필수 에이전트 프로세스
- 주요 역할

  - API Server로부터 “이 노드에 이런 Pod를 실행하라”는 명세 수신
  - 컨테이너 런타임(Docker, containerd 등)을 통해 컨테이너 생성, 실행
  - Pod 상태, 컨테이너 상태, 노드 리소스 사용량을 주기적으로 API Server에 보고
  - LivenessProbe, ReadinessProbe 등 헬스 체크 수행

- 정리

  - “노드 및 Pod 실행 담당 관리자” 역할

### kube-proxy

> Service → Pod 네트워크 트래픽을 라우팅하는 컴포넌트

- 각 노드에 배치되는 네트워크 프록시 역할
- 역할

  - Service와 Pod 간 트래픽을 적절한 Pod로 전달하는 규칙 관리
  - iptables / IPVS 등을 이용한 L4 수준 로드밸런싱 구현

- 특징

  - “모든 Pod는 다른 모든 Pod에 접근 가능”한 클러스터 네트워크를 전제로
  - Service의 ClusterIP, NodePort 등으로 들어오는 트래픽을 실제 Pod IP로 포워딩하는 구조

## Workload 오브젝트

### Pod

> Kubernetes에서 배포 가능한 가장 작은 단위 오브젝트

- 하나 이상의 컨테이너를 감싸는 논리적 그룹

  - 일반적으로는 애플리케이션 컨테이너 1개 + 사이드카 컨테이너 구조

- 특징

  - 하나의 Pod 내 컨테이너는

    - 동일 네트워크 네임스페이스 공유

      - `localhost`로 서로 통신 가능

    - 동일 볼륨 공유
    - 동일 수명주기(함께 생성되고 함께 제거)

  - Pod 자체는 “애플리케이션 인스턴스”에 해당하는 개념

- 스케일링

  - 부하 증가 시 Pod 개수(레플리카 수)를 늘리는 방식으로 확장
  - 기존 Pod에 컨테이너를 추가하는 방식이 아니라, 동일한 Pod 템플릿을 여러 개 복제하는 구조

#### Pod YAML 기본 구조

> 모든 Kubernetes 오브젝트는 YAML 기반 선언적 정의 사용

- 핵심 필드

  - `apiVersion` 리소스가 속한 API 그룹/버전
  - `kind` 오브젝트 종류 (Pod, Deployment, Service 등)
  - `metadata` 이름, 라벨 등 메타데이터
  - `spec` 실제 스펙 정의

    - `containers` 컨테이너 목록
    - 각 컨테이너의 `image`, `ports`, `env`, `volumeMounts` 등 설정

### ReplicaSet

> 동일한 Pod를 지정된 개수만큼 항상 유지해주는 컨트롤러

- 역할

  - 지정된 레플리카 수를 항상 만족시키는 역할
  - Pod가 삭제되면 자동으로 새 Pod 생성
  - Pod가 예상보다 많으면 초과분 삭제

- 구성

  - `spec.replicas` 유지할 Pod 개수
  - `spec.selector` 관리 대상 Pod 라벨
  - `spec.template` 동일하게 생성할 Pod 템플릿

- ReplicaController와 관계

  - 예전 `ReplicationController(v1)`를 대체하는 리소스
  - label selector를 더 유연하게 지원

- 실무에서의 사용 패턴

  - 직접 ReplicaSet를 관리하기보다는 Deployment가 내부적으로 생성, 관리
  - `kubectl scale`

    - `kubectl scale --replicas=6 -f replicaset-definition.yaml`
    - `kubectl scale --replicas=6 replicaset myapp-replicaset`

### Deployment

> ReplicaSet을 관리하고 롤링 업데이트, 롤백까지 책임지는 상위 컨트롤러

- 역할

  - ReplicaSet 생성 및 버전 관리
  - Pod 템플릿이 변경되면 새 ReplicaSet을 만들고, 롤링 업데이트 수행
  - 필요 시 이전 버전 ReplicaSet으로 롤백 가능

- 특징

  - Stateless 애플리케이션 배포의 기본 단위
  - `kubectl get all`로 보면 Deployment, RS, Pod가 함께 조회되는 구조

- 롤링 업데이트/롤백

  - 이미지 버전 변경 시 새 ReplicaSet 만들어 점진적으로 트래픽 이동
  - 문제가 발생하면 `kubectl rollout undo deployment/<name>`로 롤백 가능

- 생성 패턴

  - 빠른 YAML 초안 생성

    ```bash
    kubectl create deployment --image=nginx nginx \
      --dry-run=client -o yaml > nginx-deployment.yaml
    ```

    - `--dry-run=client` 실제 생성 없이 클라이언트에서만 검증
    - `-o yaml` YAML 출력 후 파일로 리다이렉트
