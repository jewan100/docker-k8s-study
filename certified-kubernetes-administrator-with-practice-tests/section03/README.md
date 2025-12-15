# Kubernetes Scheduler

> “어떤 Pod를 어떤 Node에 올릴지” 결정하는 컴포넌트

쿠버네티스의 기본 스케줄러인 `kube-scheduler`는 다음 흐름으로 동작

- 사용자가 Pod/Deployment/Job 등 워크로드를 생성 요청
- API Server가 etcd에 “스케줄되지 않은 Pod(Pending)” 로 저장
- `kube-scheduler`가 Pending Pod 목록을 확인
- 각 Node의 리소스, 라벨, taint, affinity 등을 평가해 가장 적합한 Node 선택
- 선택한 Node 이름을 Pod의 `spec.nodeName` 에 기록
- 해당 Node의 `kubelet` 이 실제로 컨테이너를 생성, 실행

### Manual Scheduling

> 스케줄러 없이 직접 Pod를 특정 Node에 고정하는 방식

- 일반적으로는 `kube-scheduler`가 자동으로 `spec.nodeName` 을 세팅하는 구조

- 테스트 목적으로 스케줄러를 끄거나, 특정 Pod를 직접 노드에 고정하고 싶다면:

  - Pod에 `nodeName` 필드를 직접 지정하는 방식

    ```yaml
    apiVersion: v1
    kind: Pod
    metadata:
      name: manual-pod
    spec:
      nodeName: worker-1 # 수동 스케줄링 대상 노드 이름
      containers:
        - name: nginx
          image: nginx
    ```

- Node가 하나도 조건에 맞지 않거나, 스케줄러가 꺼져 있는 경우

  - Pod 상태가 `Pending` 으로 유지되는 상태
  - 이벤트에 `0/3 nodes are available: ...` 같은 메시지가 남는 상태

## Labels & Selector

> “어떤 리소스를 묶어서 관리할지”를 위한 메커니즘

- Label

  - `key=value` 형태의 메타데이터
  - `metadata.labels`, `spec.template.metadata.labels` 등에 부여하는 정보

- Selector

  - 특정 Label을 가진 오브젝트 집합을 선택하는 조건
  - ReplicaSet, Deployment, Service 등이 `spec.selector` 로 사용

주의할 점

- `metadata.labels` (ReplicaSet 자신)
- `spec.template.metadata.labels` (Pod 템플릿)
- `spec.selector.matchLabels` (관리 대상 Pod 필터)

예시

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: simple-webapp
  labels:
    app: App1
    function: Front-end
spec:
  replicas: 3
  selector:
    matchLabels:
      app: App1
  template:
    metadata:
      labels:
        app: App1
        function: Front-end
    spec:
      containers:
        - name: simple-webapp
          image: simple-webapp
```

- 이 ReplicaSet은 `app=App1` 라벨을 가진 Pod만 관리 대상이 되는 구조

## Taints & Tolerations

> “어떤 Pod는 이 Node에 올리지 마라” 를 Node 기준으로 선언하는 메커니즘

### Taints

> Node에 붙이는 “이 Node에는 아무 Pod나 올리지 마라” 표시

명령 형식

```bash
kubectl taint nodes <node-name> key=value:taint-effect
```

- taint-effect

  - `NoSchedule`

    - 이 taint를 허용하는 Toleration 이 없는 Pod는 새로 스케줄되지 않는 상태

  - `PreferNoSchedule`

    - 가능하면 피하지만, 다른 선택지가 없으면 올릴 수도 있는 상태

  - `NoExecute`

    - 새 Pod 스케줄 금지 + 이미 올라가 있는 Pod도 쫓아내는 상태

- 마스터(Node) 기본 동작

  - 대부분의 배포에서 Control Plane 노드는
    `node-role.kubernetes.io/control-plane:NoSchedule` 같은 taint가 기본 설정인 상태
  - 일반 워크로드는 이 노드에 스케줄되지 않는 상태

- taint 생성, 제거

  ```bash
  # 부여
  kubectl taint nodes node1 key1=value1:NoSchedule

  # 제거
  kubectl taint nodes node1 key1=value1:NoSchedule-
  ```

### Tolerations

> 특정 taint가 있는 Node에도 이 Pod는 올라가도 된다는 “허용 조건”

- Toleration 이 있다고 해서 그 Node에 반드시 스케줄되는 것은 아님

  - “막지 않는다”는 의미
  - 실제 “가고 싶은 Node” 를 고르는 것은 Node Affinity, Scheduler 의 점수 계산 역할

예시

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    env: test
spec:
  containers:
    - name: nginx
      image: nginx
      imagePullPolicy: IfNotPresent
  tolerations:
    - key: "example-key"
      operator: "Exists"
      effect: "NoSchedule"
```

- `example-key` 라는 key 를 가진 `NoSchedule` taint가 있는 Node에도 스케줄되어도 되는 Pod 라는 의미

## Node Selector

> 가장 단순한 Node 선택 방법

- Node에 Label 부여

  ```bash
  kubectl label nodes worker-1 disktype=ssd
  ```

- Pod에서 `nodeSelector` 사용

  ```yaml
  apiVersion: v1
  kind: Pod
  metadata:
    name: nginx-ssd
  spec:
    nodeSelector:
      disktype: ssd # 이 라벨이 있는 노드에만 스케줄링
    containers:
      - name: nginx
        image: nginx
  ```

- 단순한 “key=value 완전 일치” 조건만 표현 가능

## Node Affinity

> NodeSelector 보다 더 풍부한 표현이 가능한 Node 선택 정책

- Affinity 타입

  - `requiredDuringSchedulingIgnoredDuringExecution`

    - 조건을 만족하는 Node가 필수 조건
    - 스케줄링 시점에 조건을 만족하는 Node가 없으면 Pod는 Pending 상태 유지

  - `preferredDuringSchedulingIgnoredDuringExecution`

    - 조건을 만족하는 Node를 선호
    - 없으면 다른 Node에도 스케줄 가능

- `IgnoredDuringExecution` 의미

  - Pod가 배치된 후 노드 라벨이 바뀌어 조건에 맞지 않게 되어도, 이미 동작 중인 Pod는 그대로 유지하는 동작

예시

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: with-node-affinity
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values:
                  - antarctica-east1
                  - antarctica-west1
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 1
          preference:
            matchExpressions:
              - key: another-node-label-key
                operator: In
                values:
                  - another-node-label-value
  containers:
    - name: with-node-affinity
      image: registry.k8s.io/pause:2.0
```

## Taints/Tolerations vs Node Affinity

정리하면 다음과 같습니다.

- Taints/Tolerations

  - Node가 “나는 아무나 받지 않겠다” 를 선언하는 측면
  - Toleration 이 있는 Pod만 해당 Node에 올라갈 수 있는 구조

- Node Affinity

  - Pod가 “나는 이런 Node에 가고 싶다” 를 선언하는 측면
  - 특정 라벨 조건을 만족하는 Node를 찾아 스케줄하는 구조

- 함께 사용 예

  - 중요한 시스템 Pod는

    - 특정 Node에만 올라가도록 Node Affinity 설정
    - 동시에 그 Node에 taint를 걸어 일반 워크로드는 못 올라오게 설정하는 구조

## Resource Requests & Limits

> 스케줄링과 런타임 리소스 제약을 위한 설정

- Scheduler 관점

  - Pod의 `resources.requests.cpu`, `resources.requests.memory` 를 기준으로 각 Node의 여유 리소스를 계산해서 스케줄링 수행

- Kubelet / 런타임 관점

  - `resources.limits.cpu` 를 기준으로 CPU 사용량을 제한(throttling)
  - `resources.limits.memory` 를 넘어가면 OOMKill 로 컨테이너 종료 처리

- Requests

  - 스케줄링 시점에 “이 정도는 보장해 달라” 는 최소 요구량 의미

- Limits

  - 컨테이너가 사용할 수 있는 최대량 상한선 의미

- 실행 중 리소스 변경

  - Pod 자체의 `requests/limits` 는 실행 중 직접 수정 불가
  - 일반적으로 Deployment 스펙을 수정 → 롤링 업데이트로 새로운 Pod 생성 방식 사용

## DaemonSet

> “모든 Node(또는 일부 Node)에 반드시 1개씩 Pod를 돌려라” 라는 컨트롤러

주요 사용처

- 노드 모니터링 에이전트(예: node-exporter) 배포
- 로그 수집 에이전트(예: fluentd, filebeat) 배포
- CNI 플러그인, kube-proxy 같은 노드 단위 네트워크 컴포넌트 배포

특징

- Node가 추가되면 자동으로 해당 Node에도 Pod 1개 배치
- Node가 제거되면 해당 Node의 DaemonSet Pod도 함께 제거
- “각 Node당 1개 인스턴스” 패턴에 적합한 구조

## Static Pod

> kubelet이 직접 관리하는 Pod (Control Plane 오브젝트 없이 동작)

- 정의 방식

  - 각 Node의 kubelet 설정에 지정된 디렉터리 (예: `/etc/kubernetes/manifests`) 에 YAML 파일 배치
  - kubelet이 해당 디렉터리를 주기적으로 감시하고 Pod를 생성, 재시작하는 구조

- 특징

  - API Server, ControllerManager, Scheduler 등이 없어도 kubelet 혼자서 생성, 감시 가능한 Pod 구조
  - API Server에서 “mirror Pod” 로 조회는 가능하지만, Deployment/DaemonSet 등 고수준 오브젝트와는 분리된 개념

- 사용처

  - kubeadm 기반 클러스터에서 Control Plane 컴포넌트를 Static Pod 로 올리는 패턴
  - 부팅 초기에 꼭 떠 있어야 하는 시스템 컴포넌트를 올릴 때 사용

- DaemonSet과 차이

  - DaemonSet

    - Control Plane 리소스 (API, Controller) 에 의해 관리되는 구조

  - Static Pod

    - kubelet 프로세스가 직접 관리하는 구조

## Priority Classes

> 리소스 부족 시 “어떤 Pod를 먼저 살릴지, 어떤 Pod를 먼저 내릴지” 를 정의하는 우선순위 체계

- `PriorityClass` 리소스로 우선순위 정의

  ```yaml
  apiVersion: scheduling.k8s.io/v1
  kind: PriorityClass
  metadata:
    name: high-priority
  value: 100000
  globalDefault: false
  description: "고우선순위 시스템 워크로드용 PriorityClass"
  ```

- Pod에 적용

  ```yaml
  apiVersion: v1
  kind: Pod
  metadata:
    name: important-pod
  spec:
    priorityClassName: high-priority
    containers:
      - name: app
        image: my-app
  ```

- 효과

  - 클러스터 리소스가 부족해 신규 Pod를 수용할 수 없을 때

    - 우선순위가 높은 Pod를 살리고, 낮은 Pod를 선제적으로 축출(preemption) 가능한 구조

## Multiple Schedulers

> 기본 스케줄러 외에, 특수 목적 스케줄러를 추가로 두는 패턴

- 여러 개의 스케줄러 Deployment를 띄우고, 각각 다른 `schedulerName` 을 사용해 동작시키는 구조
- Pod 정의에 `spec.schedulerName` 을 지정해서 어떤 스케줄러가 이 Pod를 처리할지 선택하는 구조
- 일반적인 클러스터에서는 기본 스케줄러 하나면 충분하며, R&D 환경이나 특수한 스케줄링 로직이 필요할 때 사용되는 영역

## Scheduler Profiles

> 하나의 kube-scheduler 안에서 플러그인 구성을 바꾸기 위한 설정

- 스케줄링 플러그인(필터, 스코어, 바인딩 등)을 조합해 하나의 profile 정의
- 다른 종류의 워크로드에 대해 서로 다른 스케줄링 정책을 적용하고 싶을 때 사용 가능한 기능
- CKA 준비, 일반 실무에서는 “이런 것이 있다” 수준 인지면 충분한 영역

## Admission Controller

> “요청이 etcd에 저장되기 전에 한 번 더 가로채서 검사, 변경하는 필터”

요청 처리 순서

1. 인증(Authentication)
2. 인가(Authorization)
3. Admission Controller
4. etcd 저장

- 역할

  - 리소스 생성, 수정 요청이 정책에 맞는지 검증하는 역할
  - 필요 시 요청 내용을 자동 수정(Mutating) 혹은 거부(Validating) 하는 역할

### Validating / Mutating Admission Controllers

- MutatingAdmissionWebhook

  - 요청 내용을 수정 가능한 Admission Controller
  - 예: Pod 생성 시 자동으로 사이드카 컨테이너 주입(istio, vault agent 등)

- ValidatingAdmissionWebhook

  - 요청을 검증만 하고, 조건에 맞지 않으면 거부하는 Admission Controller
  - 예: 특정 네임스페이스에는 privileged Pod를 금지하는 정책 등
