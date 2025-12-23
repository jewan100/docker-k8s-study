# Kubernetes Security

## Security Primitives

쿠버네티스 보안 기본 요소 정리

- 인증(Authentication)

  - “누가” 요청을 보내는지 검증하는 단계

- 인가(Authorization)

  - 인증된 주체가 “무엇을 할 수 있는지” 결정하는 단계

- TLS 통신 보호

  - 컴포넌트 간, 클라이언트–서버 간 네트워크 암호화 및 상호 신뢰 보장

- KubeConfig, API Group

  - 어떤 클러스터에 어떤 권한으로 요청할지 정의하는 클라이언트 설정 구조

- RBAC(Role/ClusterRole, \*Binding)

  - 리소스별 세밀한 권한 부여 구조

- ServiceAccount

  - 애플리케이션, CI/CD, 모니터링 도구 등이 클러스터 API를 호출할 때 사용하는 계정 구조

- Image, Runtime, Network 보안

  - 이미지 출처, 취약점, 런타임 권한, 네트워크 격리, NetworkPolicy 등 관리 구조

- Admission Controller, Pod Security

  - API 요청을 최종 반영하기 전에 정책으로 필터링, 수정하는 훅 구조

## Authentication (인증)

> [!NOTE]
> kube-apiserver는 모든 요청을 처리하기 전에 반드시 인증을 먼저 수행함

### Account 종류

- 사용자 계정(User Account)

  - 사람(admin, developer 등)이 `kubectl`, Dashboard, API 클라이언트로 접근할 때 사용하는 계정

- 서비스 계정(Service Account)

  - 애플리케이션, 컨트롤러, CI/CD 도구(Prometheus, Jenkins 등)가 클러스터와 상호작용할 때 사용하는 계정

### 대표적인 인증 방식

- 클라이언트 인증서(X.509)

  - kubeconfig에 client certificate, client key를 넣어두고 mTLS를 사용하는 방식

- Bearer Token (예: ServiceAccount Token)

  - `Authorization: Bearer <token>` 헤더로 전달하는 토큰 기반 인증

- Static Token File / Basic Auth

  - 옛날 방식, 파일에 id/token을 평문으로 저장
  - 학습/테스트 환경 이외에는 사용 지양

- 외부 Identity Provider 연동

  - OIDC, LDAP, SSO, Webhook 등과 연계해서 인증하는 구조

## TLS Certificates

### TLS 개념

- 통신 암호화, 무결성, 서버/클라이언트 신원 확인 목적
- 비대칭 암호화 기반

  - 비공개키(Private Key)

    - 외부에 절대 노출하면 안 되는 키

  - 공개키(Public Key)

    - 인증서에 포함되어 배포되는 키

- 서버는 비공개키로 서명, 클라이언트는 공개키로 검증하는 구조

### Kubernetes에서의 주요 인증서

kubeadm 기준 기본 경로: `/etc/kubernetes/pki`

- 클러스터 루트 CA

  - `ca.crt`, `ca.key`
  - 클러스터 내부 다른 인증서를 서명하는 최상위 인증 기관 역할

- apiserver 서버 인증서

  - `apiserver.crt`, `apiserver.key`
  - `https://<control-plane ip>:6443` 등에 대해 서버 신원 보장

- apiserver → kubelet 통신용 클라이언트 인증서

  - `apiserver-kubelet-client.crt`, `apiserver-kubelet-client.key`

- etcd 서버 / 피어 인증서

  - `etcd/server.crt`, `etcd/server.key`

    - 클라이언트(API Server 등)가 etcd에 접속할 때 사용하는 서버 인증서

  - `etcd/peer.crt`, `etcd/peer.key`

    - etcd 노드 간(클러스터 구성 시) 상호 TLS 통신용 인증서

- front-proxy, controller-manager, scheduler, kubelet 등

  - 각 컴포넌트별 클라이언트/서버 인증서 + CA 구성

## Certification Authority (CA)

- 클러스터 내 각종 인증서를 서명하는 신뢰의 기준 역할
- 루트 CA만 실제 비공개키를 가지며, 모든 서버/클라이언트 인증서는 CA의 서명을 통해 신뢰 사슬을 만듦
- kubeadm 클러스터에서는 `/etc/kubernetes/pki/ca.crt`, `/etc/kubernetes/pki/ca.key` 가 기본 루트

## KubeConfig 파일

`kubectl` 이 어떤 클러스터에, 어떤 사용자로, 어떤 네임스페이스에, 어떤 인증서를 써서 붙을지 정의하는 설정 파일

- clusters

  - API Server 주소, 서버 인증서(CA) 등 클러스터 정보

- users

  - 인증서/토큰/Exec 플러그인 등을 포함한 사용자 또는 서비스 계정 정보

- contexts

  - `(cluster, user, namespace)` 조합
  - 현재 작업 대상 컨텍스트 선택

```bash
kubectl config view               # 전체 kubeconfig 조회
kubectl config get-contexts       # 컨텍스트 목록 조회
kubectl config use-context dev    # dev 컨텍스트로 전환
```

## API Group

- Kubernetes API 엔드포인트는 그룹/버전/리소스 구조로 구분

- Core(API v1)

  - `/api/v1`
  - Pod, Service, ConfigMap, Secret 등 기본 리소스

  - `/apis/apps/v1` → Deployment, StatefulSet, DaemonSet, ReplicaSet 등
  - `/apis/rbac.authorization.k8s.io/v1` → Role, ClusterRole 등
  - `/apis/networking.k8s.io/v1` → NetworkPolicy, Ingress 등

## Authorization (인가)

> 인증 후 “이 요청을 허용할 것인가?”를 결정하는 단계

### Authorization Mode

- Node

  - kubelet이 자신이 속한 Pod/Node 관련 리소스만 접근하도록 제한하는 모드

- ABAC(Attribute Based Access Control)

  - JSON 파일로 규칙을 정의하는 옛 방식, 거의 사용하지 않음

- RBAC(Role Based Access Control)

  - Role/ClusterRole 기반 권한 제어, 현재 사실상 표준

- Webhook

  - 외부 권한 시스템에 질의해서 허용/거부를 결정하는 모드

## RBAC: Role, ClusterRole, RoleBinding, ClusterRoleBinding

### Role / RoleBinding

- Role

  - 특정 네임스페이스 안에서의 권한 정의 리소스
  - 예: `default` 네임스페이스 안에서 Pod 읽기/생성 권한

- RoleBinding

  - 사용자/ServiceAccount와 Role을 연결하는 리소스

예시

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: dev
rules:
  - apiGroups: [""] # core API group
    resources: ["pods"]
    verbs: ["get", "list", "watch"]

apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: dev
subjects:
  - kind: User
    name: dev-user # 인증된 사용자 이름
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### ClusterRole / ClusterRoleBinding

- ClusterRole

  - 네임스페이스에 종속되지 않는 권한 묶음
  - `nodes`, `persistentvolumes` 처럼 클러스터 전체 리소스나, 여러 네임스페이스에 동일 권한을 부여할 때 사용

- ClusterRoleBinding

  - 사용자/ServiceAccount와 ClusterRole을 클러스터 전역에서 바인딩

예시

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: pod-reader-all-namespaces
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-pods-global
subjects:
  - kind: User
    name: dev-user
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: pod-reader-all-namespaces
  apiGroup: rbac.authorization.k8s.io
```

```bash
# dev-user가 default 네임스페이스에서 pods 생성 가능한지 확인
kubectl auth can-i create pods --as dev-user -n default

# 클러스터 전역에서 노드 조회 가능한지 확인
kubectl auth can-i get nodes --as dev-user
```

## ServiceAccount

- User Account

  - 사람 기준 계정, 클러스터 외부에서 API를 호출하는 주체

- ServiceAccount

  - Pod 내 애플리케이션, 컨트롤러, CI/CD 도구 등 “기계”가 API를 호출할 때 사용하는 계정

- 각 네임스페이스마다 `default` ServiceAccount 자동 생성
- Pod를 만들 때 별도 지정하지 않으면 `default` ServiceAccount가 자동으로 할당

```bash
kubectl get serviceaccount
kubectl create serviceaccount app-sa -n dev
```

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-sa-pod-read
  namespace: dev
subjects:
  - kind: ServiceAccount
    name: app-sa
    namespace: dev
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Pod에서 ServiceAccount 지정

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
  namespace: dev
spec:
  serviceAccountName: app-sa
  containers:
    - name: app
      image: my/app:latest
```

## Image Security

- Private Registry 사용

  - 사내 레지스트리, ECR, GCR 등 사용
  - `imagePullSecrets` 로 인증 정보 제공

예시

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: private-reg
spec:
  containers:
    - name: app
      image: my-registry.example.com/my-team/my-image:1.0.0
  imagePullSecrets:
    - name: regcred
```

`regcred` 생성 예시(도커 레지스트리 기준)

```bash
kubectl create secret docker-registry regcred \
  --docker-server=my-registry.example.com \
  --docker-username=<username> \
  --docker-password=<password> \
  --docker-email=<email>
```

## Network Security

기본 CNI 플러그인만 있는 상태에서는 “Pod 간 모든 트래픽 허용”이 일반적인 초기 상태NetworkPolicy 는 Pod 간/Pod↔외부 간 네트워크 트래픽을 제한하는 리소스

- 사용 중인 CNI 플러그인이 NetworkPolicy를 지원해야 실제로 동작

### NetworkPolicy 예시 분석

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: test-network-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      role: db
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - ipBlock:
            cidr: 172.17.0.0/16
            except:
              - 172.17.1.0/24
        - namespaceSelector:
            matchLabels:
              project: myproject
        - podSelector:
            matchLabels:
              role: frontend
      ports:
        - protocol: TCP
          port: 6379
  egress:
    - to:
        - ipBlock:
            cidr: 10.0.0.0/24
      ports:
        - protocol: TCP
          port: 5978
```

- `podSelector: role=db`

  - `role=db` 라벨을 가진 Pod에 이 정책 적용

- `policyTypes: Ingress, Egress`

  - 들어오는 트래픽, 나가는 트래픽 둘 다 제어

- Ingress 규칙

  - 아래 중 하나에 해당하는 소스에서만 6379/TCP 접근 허용

    - 172.17.0.0/16 대역 IP 중 172.17.1.0/24 제외
    - 라벨 `project=myproject` 네임스페이스
    - 라벨 `role=frontend` Pod

- Egress 규칙

  - 10.0.0.0/24 대역의 5978/TCP 로 나가는 트래픽만 허용

- 특정 Pod에 대해 NetworkPolicy가 하나라도 적용되면, 명시적으로 허용된 것 외에는 기본 차단 구조
- “외부로 나가는 트래픽만 막는다” 같은 세밀한 제어를 위해 Egress 규칙을 함께 정의하는 패턴 사용
