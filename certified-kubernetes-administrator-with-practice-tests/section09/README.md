# Kubernetes Network

## CNI(Container Network Interface)

> 쿠버네티스가 “네트워크를 직접 구현하지 않고”, 플러그인에게 위임하기 위해 정의한 표준 인터페이스

- CNI는 컨테이너가 생성·삭제될 때 네트워크를 어떻게 붙일지 정의하는 표준 사양
- kubelet은 Pod를 만들 때 CNI 플러그인을 호출해서

  - Pod IP 할당
  - veth 생성 및 브리지 연결
  - 라우팅, iptables 설정
    같은 작업을 수행함

- 실제 구현체는 플러그인

  - Flannel, Calico, Cilium, Weave Net 등 CNI 플러그인

- 쿠버네티스 네트워크 모델 자체는 “모든 Pod 간 완전 통신”을 요구할 뿐이고,
  그 요구사항을 어떻게 만족시킬지는 CNI 플러그인이 담당하는 구조

## Pod Networking

> Pod와 Pod 간 통신, Pod와 Node 간 통신 구조를 정의하는 계층

쿠버네티스 네트워크 모델의 핵심 가정

- 모든 Pod는 클러스터 내에서 유일한 IP를 가져야 하는 구조
- 어떤 Pod든지, 다른 모든 Pod와 NAT 없이 직접 통신 가능해야 하는 구조
- 같은 Node 안의 Pod뿐 아니라, 다른 Node의 Pod와도 동일한 IP로 통신 가능해야 하는 구조

### Pod 내부 네트워크 구조

- 하나의 Pod 안에 있는 모든 컨테이너는

  - 동일 네트워크 네임스페이스 공유
  - 동일 IP, 동일 포트 공간 공유
    따라서 `localhost:포트` 로 서로 호출 가능

- 컨테이너별로 다른 IP를 가지지 않고, Pod 단위로 IP가 부여되는 모델

### Pod 간 통신 흐름

- 같은 Node 내 Pod 간 통신

  - veth pair와 브리지(cni0 등)를 통해 L2 수준에서 바로 통신하는 구조

- 다른 Node 간 Pod 통신

  - CNI 플러그인이 설정한 오버레이 네트워크(Flannel VXLAN 등) 또는 라우팅 설정을 통해 IP 라우팅
  - Pod는 상대 Pod의 IP만 알면 되고, Node 간 라우팅은 CNI가 처리하는 구조

### 외부로 나가는 트래픽

- Pod → 인터넷 통신

  - 일반적으로 Node의 IP로 SNAT 되어 나가는 구조
  - Node의 iptables 또는 IPVS 규칙을 통해 외부로 라우팅되는 구조

- 외부 클라이언트 → Pod 직접 접근

  - 기본적으로는 불가능한 구조
  - Service(NodePort, LoadBalancer), Ingress 등을 통해 노출하는 패턴 사용

요약하면, Pod 네트워킹은 클러스터 내부 평면을 만드는 계층이고,
CNI 플러그인이 “Pod에게 IP를 주고, Pod 간/Node 간 라우팅을 맞추는 역할”을 담당하는 구조

## Service Networking

> Pod가 바뀌어도 “항상 같은 엔드포인트로 접근”할 수 있게 하는 가상 IP 계층

Pod만으로는 네트워크적으로 불안정함

- Pod는 재시작되면 IP가 바뀔 수 있는 리소스
- 스케일 인·아웃 시 Pod 수가 계속 변하는 리소스

그래서 Service라는 추상화가 필요함

- 특정 라벨 셀렉터에 매칭되는 Pod 집합을 “하나의 서비스”로 묶는 추상화
- Service가 고정 가상 IP(ClusterIP)와 가상 포트를 제공
- `kube-proxy`가 iptables/IPVS를 이용해서 Service IP로 들어온 트래픽을 실제 Pod IP로 로드밸런싱하는 구조

### ClusterIP

- 기본 Service 타입
- 클러스터 내부에서만 접근 가능한 가상 IP 제공
- 다른 Pod는 `http://<service-name>:<port>` 또는 `ClusterIP:Port` 로 접근
- 내부 MSA 간 통신, 내부 API 서버 등에 사용되는 타입

### NodePort

- 각 Node의 특정 포트를 열어 외부에서 직접 접근하도록 하는 타입
- 외부 클라이언트는 `http://<노드IP>:<NodePort>` 로 접근
- 간단한 테스트용, 온프레미스 환경에서 L4 로드밸런서가 없을 때 자주 사용하는 타입

### LoadBalancer

- 클라우드 프로바이더(GKE, EKS, AKS 등)와 연동되는 타입
- Service 앞단에 클라우드 L4 로드밸런서를 자동 생성
- 외부 IP 또는 도메인 하나로 여러 Node의 NodePort에 로드밸런싱하는 구조
- 로컬(minikube)에서는 실제 L4가 없으므로 `minikube service` 명령으로 프록시 방식 사용

서비스 네트워킹은 요약하면 ClusterIP로 내부 통신 안정화, NodePort/LoadBalancer로 외부 진입점 제공 구조

## Cluster DNS와 CoreDNS

> “서비스 이름 기반 통신”을 가능하게 해주는 DNS 계층

### CoreDNS

- `kube-system` 네임스페이스에 Deployment로 배치되는 DNS 서버 역할
- Service, Pod 정보를 감시해 DNS 레코드로 노출하는 역할
- 각 Pod의 `/etc/resolv.conf` 는 CoreDNS Service(IP)로 기본 설정

### Service DNS 패턴

```text
<service-name>.<namespace>.svc.cluster.local
```

```text
users-service.default.svc.cluster.local
```

- `users-service` Service 이름
- `default` 네임스페이스
- `svc` Service 도메인
- `cluster.local` 클러스터 기본 도메인

- 같은 네임스페이스

  - `users-service`

- 다른 네임스페이스 명시

  - `users-service.backend`

CoreDNS가 있기 때문에 Pod는 IP를 전혀 모른 채 “서비스 이름”만으로 통신할 수 있고,
IP 변경, 스케일 인·아웃이 발생해도 어플리케이션 코드를 바꿀 필요가 없는 구조
