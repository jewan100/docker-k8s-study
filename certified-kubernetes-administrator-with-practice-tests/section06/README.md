# Cluster Maintenance

## OS Upgrades (노드 OS 업그레이드)

노드 OS 패치나 커널 업데이트를 할 때는, 해당 노드에서 워크로드를 안전하게 빼낸 뒤 작업하는 흐름으로 운영함.

### 주요 명령

```bash
# 새 Pod 스케줄링만 막기 (기존 Pod는 그대로 유지)
kubectl cordon node-1

# 기존 Pod를 다른 노드로 안전하게 옮기기
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data

# OS 패치, 재부팅 등 수행

# 다시 스케줄링 허용
kubectl uncordon node-1
```

- `cordon`

  - 노드를 `Unschedulable` 상태로 표시하는 명령
  - 새로운 Pod가 해당 노드로 배치되지 않도록 막는 제어

- `drain`

  - 해당 노드에 올라가 있는 일반 Pod를 모두 축출(evict)하는 명령
  - 같은 ReplicaSet/Deployment에 속한 다른 노드로 Pod를 재배치하도록 유도하는 절차
  - `--ignore-daemonsets` 옵션으로 DaemonSet Pod는 그대로 유지하는 패턴
  - `--delete-emptydir-data` 옵션으로 emptyDir 데이터를 삭제하는 것에 동의하는 표시

- `uncordon`

  - 노드를 다시 스케줄링 가능 상태로 되돌리는 명령

운영 패턴

1. `cordon + drain`으로 워크로드를 비운 뒤
2. OS 패치 및 재부팅 수행
3. `uncordon`으로 다시 트래픽을 받게 하는 순서

## Cluster Upgrade (kubeadm 기준)

[Upgrading kubeadm clusters](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/) \
[Upgrading Linux nodes](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/upgrading-linux-nodes/)

### 1. 사전 작업

- 업그레이드 대상 버전 결정
- `kubeadm upgrade plan` 으로

  - 현재 컨트롤 플레인 버전 확인
  - 업그레이드 가능한 타깃 버전 목록 확인
  - 애드온 호환성 검토

### 2. 리포지터리 버전 고정

컨트롤 플레인 노드에서 Kubernetes apt 리포지터리 버전을 타깃 버전에 맞게 변경.

```bash
sudo vi /etc/apt/sources.list.d/kubernetes.list
# 예: 1.34 계열로 변경
```

### 3. 컨트롤 플레인 노드 업그레이드

```bash
# kubeadm 먼저 업그레이드
sudo apt-mark unhold kubeadm && \
sudo apt-get update && \
sudo apt-get install -y kubeadm='1.34.x-*' && \
sudo apt-mark hold kubeadm

# 실제 컨트롤 플레인 업그레이드
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.34.x
```

- `kubeadm upgrade apply`

  - API Server, Controller Manager, Scheduler, etcd 등 컨트롤 플레인 컴포넌트 버전 업그레이드 작업
  - static Pod manifest 수정 및 관련 설정 갱신 과정

컨트롤 플레인 노드에서 kubelet, kubectl도 동일 버전으로 맞춤.

```bash
sudo apt-mark unhold kubelet kubectl && \
sudo apt-get update && \
sudo apt-get install -y kubelet='1.34.x-*' kubectl='1.34.x-*' && \
sudo apt-mark hold kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

> 요약
>
> - 컨트롤 플레인 노드: `kubeadm upgrade apply` 사용
> - 워커 노드: `kubeadm upgrade node` 사용

### 4. 워커 노드 업그레이드

각 워커 노드는 하나씩 순차적으로 처리하는 패턴.

1. 워커 노드에서 워크로드 비우기

```bash
kubectl drain node-1 --ignore-daemonsets --delete-emptydir-data
```

2. 해당 노드에 SSH 접속 후

```bash
# kubeadm 업그레이드
sudo apt-mark unhold kubeadm && \
sudo apt-get update && \
sudo apt-get install -y kubeadm='1.34.x-*' && \
sudo apt-mark hold kubeadm

# 노드 구성 업그레이드
sudo kubeadm upgrade node

# kubelet, kubectl 업그레이드
sudo apt-mark unhold kubelet kubectl && \
sudo apt-get update && \
sudo apt-get install -y kubelet='1.34.x-*' kubectl='1.34.x-*' && \
sudo apt-mark hold kubelet kubectl

sudo systemctl daemon-reload
sudo systemctl restart kubelet
```

3. 다시 스케줄링 허용

```bash
kubectl uncordon node-1
```

같은 작업을 `node-2`, `node-3` 등 모든 워커 노드에 반복 수행하는 구조.

## Backup and Restore Methods

### etcd Backup

etcd는 클러스터의 모든 상태 정보가 저장되는 핵심 컴포넌트.
`etcdctl`을 이용해 스냅샷 단위로 백업을 수행하는 패턴.

#### 스냅샷 저장

```bash
# v3 API 사용
export ETCDCTL_API=3

etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /backup/etcd-snapshot.db
```

- `--endpoints`

  - 접속할 etcd 서버 주소 지정

- `--cacert`, `--cert`, `--key`

  - TLS 인증서 지정
  - kubeadm 환경 기준 `/etc/kubernetes/pki/etcd/` 경로에 위치하는 파일 사용

- `snapshot save`

  - 현재 시점의 etcd 데이터를 파일로 덤프하는 명령

추가적으로 스냅샷 상태를 확인할 때

```bash
etcdctl snapshot status /backup/etcd-snapshot.db
```

### etcd Restore

etcd를 특정 시점 스냅샷으로 복구할 때 사용하는 절차.

대표적인 흐름

1. API Server 정지

```bash
# static Pod 기반일 경우, manifest를 일시적으로 이동하거나 systemd 유닛 정지
sudo systemctl stop kube-apiserver
```

2. etcd 스냅샷 복구

```bash
export ETCDCTL_API=3

etcdctl snapshot restore /backup/etcd-snapshot.db \
  --data-dir=/var/lib/etcd-from-backup
```

- `--data-dir`

  - 복구된 etcd 데이터가 저장될 새 디렉터리 경로
  - 기존 `/var/lib/etcd` 대신 새로운 디렉터리를 사용하는 패턴

3. etcd 데이터 디렉터리 포인터 변경

- `/etc/kubernetes/manifests/etcd.yaml` (kubeadm 기준 static Pod manifest) 파일에서

  - `--data-dir=/var/lib/etcd-from-backup` 로 변경

- 또는 systemd 기반 외부 etcd일 경우, 서비스 유닛의 `--data-dir` 수정

4. etcd 및 API Server 재시작

```bash
sudo systemctl daemon-reload
sudo systemctl restart etcd
sudo systemctl start kube-apiserver
```

복구 후에는

- `kubectl get nodes`, `kubectl get pods -A` 등으로 클러스터 상태 확인
- 필요한 경우 애드온 및 애플리케이션 레벨에서 데이터 일관성 추가 검증 수행 구조
