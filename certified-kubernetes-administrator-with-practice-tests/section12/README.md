# Helm

> Kubernetes 애플리케이션 패키지 매니저

Helm은 Kubernetes 리소스 묶음(Deployment, Service, ConfigMap 등)을 하나의 패키지(Chart)로 관리하고,
설치, 업그레이드, 롤백 이력까지 관리하기 위한 도구

## Helm이 필요한 이유

- 매니페스트 파일 폭증 문제 해결용 패키징 도구
  (deployment.yaml, service.yaml, configmap.yaml 등 파일 수십 개 관리 부담 완화 목적)
- 환경별 설정 분리 필요성
  (dev, stage, prod 별 이미지 태그, 리소스, URL 등을 values 파일로 분리 관리 필요성)
- 배포 이력 관리 및 롤백 필요성
  (버전별 릴리스 이력, Rollback 지원 필요성)
- 재사용 가능한 애플리케이션 템플릿 공유 필요성
  (공개 차트 레포에서 DB, 메시지 브로커, 워드프레스 등 바로 설치 활용 목적)

## 기본 개념

- Chart
  애플리케이션을 구성하는 Kubernetes 리소스 템플릿 묶음
- Release
  특정 Chart를 실제 클러스터에 설치한 인스턴스 단위
- Repository
  Chart 패키지를 저장, 배포하는 원격 저장소
- Values
  Chart 템플릿에 주입되는 설정 값 집합
- Template Engine
  Go 템플릿 기반으로 values를 주입해 실제 YAML을 생성하는 엔진

```bash
helm install wordpress bitnami/wordpress
helm upgrade wordpress bitnami/wordpress
helm rollback wordpress 2
```

- `wordpress`
  Release 이름
- `bitnami/wordpress`
  Chart 이름(레포/차트)
- upgrade, rollback은 같은 Release를 대상으로 버전만 교체하는 동작 구조

## Helm 구성 요소

### Chart & Repository

- Chart

  - 특정 애플리케이션 배포 단위 패키지
  - 버전(semver)으로 관리

- Repository

  - 여러 Chart를 묶어 제공하는 HTTP 기반 저장소
  - 예: `https://charts.bitnami.com/bitnami`

### Kubernetes Cluster

- Helm v3 기준 별도 서버 컴포넌트(Tiller) 없음
- Helm CLI가 kubeconfig를 사용해 API Server와 직접 통신해서 리소스 생성, 수정, 삭제 수행

## Helm Chart

> Kubernetes 리소스를 패키징한 디렉터리/압축 파일 구조

### Chart 구조 예시

```text
myapp/
  Chart.yaml        # 차트 메타데이터(이름, 버전, 설명 등)
  values.yaml       # 기본 값 정의
  templates/        # 실제 Kubernetes 리소스 템플릿
    deployment.yaml
    service.yaml
    configmap.yaml
    _helpers.tpl    # 공통 템플릿 함수/조각 정의
```

- `Chart.yaml`

  - 차트 이름, 버전, 설명, 유지보수자 정보 등 메타데이터

- `values.yaml`

  - 공통 기본 설정 값
  - 예: 이미지 리포지터리, 태그, 리소스, 환경변수 값 등

- `templates/*.yaml`

  - 실제 Kubernetes 리소스 템플릿 파일
  - Go 템플릿 문법(`{{ .Values.image.repository }}` 등) 사용

- `_helpers.tpl`

  - 이름 규칙, 공통 라벨 등 반복 로직 캡슐화 템플릿 정의 파일

### values 오버라이드

환경별로 값 분리 예시:

```bash
# 기본 값(개발용)
helm install myapp ./myapp

# 운영 환경 값 오버라이드
helm install myapp ./myapp -f values-prod.yaml
helm upgrade myapp ./myapp -f values-prod.yaml
```

또는 간단한 값은 `--set`으로 인라인 지정

```bash
helm install myapp ./myapp \
  --set image.tag=v2.0.0 \
  --set replicaCount=3
```

## Helm CLI

### Repository 관리

```bash
# 레포 추가
helm repo add bitnami https://charts.bitnami.com/bitnami

# 레포 목록
helm repo list

# 레포 인덱스 최신화
helm repo update
```

### Chart 검색

```bash
# 추가된 레포 내에서 검색
helm search repo wordpress

# Helm Hub(artifact hub) 전체에서 검색
helm search hub wordpress
```

- `helm search repo`

  - 로컬에 등록된 레포 범위 내 검색

- `helm search hub`

  - 중앙 허브(Artifact Hub)에 등록된 다양한 퍼블릭 레포에서 검색

### 설치(install)

```bash
# 공용 레포의 Wordpress 차트 설치
helm install wordpress bitnami/wordpress

# 로컬 차트 디렉터리 설치
helm install myapp ./myapp

# 네임스페이스 지정 설치
helm install myapp ./myapp -n backend --create-namespace

# values 파일 지정 설치
helm install myapp ./myapp -f values-prod.yaml
```

- 첫 번째 인자: Release 이름
- 두 번째 인자: Chart 경로 또는 `<repo>/<chart>` 형식

### 업그레이드(upgrade)

```bash
# 새로운 이미지 태그로 업그레이드
helm upgrade myapp ./myapp --set image.tag=v2.0.0

# values 파일 변경으로 업그레이드
helm upgrade myapp ./myapp -f values-prod.yaml
```

- 동일 Release 이름에 대해 새로운 Chart/values로 다시 적용하는 동작
- 내부적으로는 새 리비전 생성 및 롤링 업데이트 수행

### 상태/이력 조회

```bash
# 현재 클러스터에 배포된 Release 목록
helm list
helm list -A        # 모든 네임스페이스

# 특정 Release 상태
helm status myapp

# 특정 Release 배포 이력
helm history myapp
```

### 롤백(rollback)

```bash
# 직전 리비전으로 롤백
helm rollback myapp

# 특정 리비전으로 롤백
helm rollback myapp 3
```

- Deployment의 `kubectl rollout undo` 와 유사하지만, Helm 단위로 전체 리소스 묶음 상태를 롤백하는 개념

### 삭제(uninstall)

```bash
# Release 단위 삭제
helm uninstall myapp

# 네임스페이스 지정
helm uninstall myapp -n backend
```

- 해당 Release가 생성했던 Kubernetes 리소스를 정리
- 이력 정보도 함께 제거

### 템플릿 렌더링(template)

```bash
# 실제 적용하지 않고 템플릿만 로컬에서 렌더링
helm template ./myapp

# 특정 Release 이름, values와 함께 렌더링
helm template myapp ./myapp -f values-prod.yaml
```

- 실제 `kubectl apply` 전에 생성될 YAML을 눈으로 확인하고 싶을 때 사용
- GitOps 파이프라인에서 `helm template` 결과를 다시 관리하는 패턴도 존재

### 기타 유용한 명령

```bash
# 차트 유효성 검사
helm lint ./myapp

# 차트 메타데이터 보기
helm show chart bitnami/wordpress

# 차트 기본 values 보기
helm show values bitnami/wordpress
```
