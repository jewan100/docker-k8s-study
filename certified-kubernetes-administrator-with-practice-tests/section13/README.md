# Kustomize

> 같은 리소스 구조를 유지한 채, 환경별(dev, stg, prod) 설정만 “레이어처럼” 덧입히는 도구

- 쿠버네티스 YAML을 “복사·붙여넣기”로 환경별로 여러 벌 만드는 비효율을 줄이기 위한 도구
- `kustomization.yaml` 하나를 기준으로, 여러 리소스(YAML)를 조합·변형하는 방식
- Helm처럼 패키징/배포 + 템플릿 언어를 제공하는 것이 아니라, 순수 YAML + 패치/트랜스포머에 집중하는 구조

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
```

## Kustomize vs Helm

- 공통점

  - 여러 YAML 파일을 묶어서 환경별 설정을 바꾸고, 하나의 최종 매니페스트를 만든다는 점은 동일

### Helm

- Go template(`{{ .Values.xxx }}`) 기반 템플릿 엔진
- Chart 패키징, 버전 관리, 의존성 관리, 설치/업그레이드/롤백 등 “패키지 매니저” 역할 포함
- values 파일로 환경별 값을 주입하는 방식
- 템플릿 문법이 섞여서, YAML이 실제 렌더링 전까지 눈으로 파악하기 어려운 경우가 있음

### Kustomize

- 순수 YAML + Kustomization 레이어 구조
- 템플릿 언어 없이, 패치(patch) 와 트랜스포머(transformer) 로만 조합
- “환경별로 설정만 조금씩 다르게” 가져가고 싶을 때 단순하고 직관적인 구조
- `kubectl apply -k` 로 바로 연동 가능

## Kustomize CLI

> `kustomization.yaml` 을 기준으로 리소스를 빌드하고, kubectl 과 파이프로 연결하는 사용 방식

### 기본 명령

- 로컬에서 결과만 확인

  ```bash
  kustomize build k8s/
  ```

- 빌드 결과를 그대로 적용

  ```bash
  kustomize build k8s/ | kubectl apply -f -
  ```

- 빌드 결과를 기준으로 삭제

  ```bash
  kustomize build k8s/ | kubectl delete -f -
  ```

### kubectl 연동(`-k` 플래그)

- 별도 kustomize 바이너리 없이, kubectl 만으로도 사용 가능

  ```bash
  kubectl apply -k k8s/
  kubectl delete -k k8s/
  ```

- `-f` 대신 `-k` 를 쓰면, 해당 디렉터리 내 `kustomization.yaml` 을 읽어 전체 리소스를 조합해서 적용

## Multiple Directories 구조

> “폴더로 리소스를 분리하고, 상위에서 다시 묶는” 기본 패턴

### 단일 kustomization.yaml 에서 리소스 나열

```yaml
# k8s/kustomization.yaml
resources:
  - api/api-depl.yaml
  - api/api-service.yaml
  - db/db-depl.yaml
  - db/db-service.yaml
```

### 폴더 단위 kustomization 으로 재사용

각 서브 디렉터리에 별도 `kustomization.yaml`을 두고, 상위에서 디렉터리만 참조하는 방식

```yaml
# api/kustomization.yaml
resources:
  - api-depl.yaml
  - api-service.yaml
```

```yaml
# db/kustomization.yaml
resources:
  - db-depl.yaml
  - db-service.yaml
```

```yaml
# base/kustomization.yaml
resources:
  - api/
  - db/
  - cache/
  - kafka/
```

- `api/` 디렉터리 하나만 떼어서 테스트도 가능
- `base/` 에 공통 정의를 모아두고, 환경별 dev/stg/prod 오버레이에서 그대로 재사용하는 구조로 확장 가능

## Transformers

> Kustomize 가 제공하는 “공통 설정 자동 삽입/변경기” 개념

### Common Transformers

공통 라벨, 네임스페이스, 이름 접두/접미어 등을 한 번에 주입하는 기능

- `labels`

  ```yaml
  labels:
    - pairs:
        app: my-app
        env: dev
  ```

- `namePrefix` / `nameSuffix`

  ```yaml
  namePrefix: dev-
  nameSuffix: -v1
  ```

  - Deployment, Service 등의 이름에 `dev-`, `-v1` 을 자동 부착
  - 이름 충돌 방지, 환경 구분에 유용

- `namespace`

  ```yaml
  namespace: my-namespace
  ```

  - 모든 리소스에 네임스페이스를 일괄 지정
  - YAML 개별 파일에 namespace 를 안 써도 되는 구조

- `commonAnnotations`

  ```yaml
  commonAnnotations:
    maintainer: "jewan"
    managed-by: "kustomize"
  ```

  - 공통 어노테이션을 모든 리소스에 일괄 추가

### Image Transformer

> 이미지 이름/태그를 환경별로 바꾸고 싶을 때 사용하는 설정

- 기본 이미지 정의 (Deployment 등)

  ```yaml
  containers:
    - name: api
      image: my-registry/api:latest
  ```

- Kustomization 에서 이미지 변경

  ```yaml
  images:
    - name: my-registry/api
      newName: my-registry/api
      newTag: "2.4.0"
  ```

- 이름 자체 교체

  ```yaml
  images:
    - name: nginx
      newName: haproxy
  ```

- 이름 + 태그 동시 변경

  ```yaml
  images:
    - name: api
      newName: my-registry/api
      newTag: "2.4.0"
  ```

## Patches

> 기존 YAML 리소스에 “부분 변경” 을 선언적으로 추가하는 기능

Kustomize 에서는 두 가지 주요 패치 스타일을 지원

1. JSON Patch (RFC 6902)
2. Strategic Merge Patch(SMP)

### JSON Patch (RFC 6902)

> “어느 리소스의 어떤 경로를, 어떻게 바꿀지” 를 절대 경로 기반으로 지정하는 방식

- 패치 정의 예시

```yaml
patches:
  - target:
      kind: Deployment
      name: api-deployment
    patch: |-
      - op: replace
        path: /spec/replicas
        value: 5
```

- 의미

  - `kind: Deployment`, `name: api-deployment` 인 리소스를 찾아
  - `/spec/replicas` 값을 `5`로 교체

- 별도 파일로 분리하는 패턴

```yaml
# kustomization.yaml
patches:
  - path: replica-patch.yaml
    target:
      kind: Deployment
      name: nginx-deployment
```

```yaml
# replica-patch.yaml (JSON Patch 형식)
- op: replace
  path: /spec/replicas
  value: 5
```

- `add` 새 필드 추가
- `replace` 기존 필드 값 교체
- `remove` 필드 제거

### Strategic Merge Patch(SMP)

> 기본 리소스와 “부분 YAML” 을 병합하는 방식, 사람이 읽기·유지하기 좀 더 편한 스타일

- inline 패치 예시

```yaml
patches:
  - patch: |-
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        name: api-deployment
      spec:
        replicas: 5
```

- 별도 파일로 분리하는 패턴

```yaml
# kustomization.yaml
patches:
  - replica-patch.yaml
```

```yaml
# replica-patch.yaml (SMP 형식)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-deployment
spec:
  replicas: 5
```

- 기존 spec 구조와 병합되는 방식

  - 명시된 필드는 override
  - 지정하지 않은 필드는 기본값 유지

- 삭제 연산은 `$patch: delete` 등을 사용해 표현 가능

## Overlays

> base(공통) 위에 dev/stg/prod 환경별로 추가 패치/트랜스폼을 “오버레이” 하는 구조

### 기본 구조 예시

```text
k8s/
  base/
    kustomization.yaml
    api/
    db/
  overlays/
    dev/
      kustomization.yaml
    stg/
      kustomization.yaml
    prod/
      kustomization.yaml
```

`base/kustomization.yaml`

```yaml
resources:
  - api/
  - db/
```

`overlays/dev/kustomization.yaml`

```yaml
bases:
  - ../../base

namePrefix: dev-

images:
  - name: my-registry/api
    newTag: "1.0.0-dev"

patches:
  - replica-patch.yaml
```

`bases`(현재는 `resources`로 통합 사용하는 패턴이 많지만, 개념적으로는 base를 참조하는 역할)

- base 에서 정의한 리소스를 그대로 가져와 dev 환경 입력으로 사용
- dev 환경에서는 prefix, 이미지 태그, replicas 등을 별도로 덮어씀

운영 방식

- `kubectl apply -k overlays/dev`
- `kubectl apply -k overlays/prod`

이렇게 환경별로 별도의 디렉터리를 apply 하여 배포

## Components

> 여러 Kustomization 에서 재사용 가능한 “부분 모듈” 개념

- 공통적으로 끼워 넣고 싶은 리소스 집합을 Component 로 정의

  - 예: 공통 로그 수집 DaemonSet, 공통 모니터링 설정, 공통 NetworkPolicy 묶음 등

- base/overlay 와는 별개로, “옵션처럼 추가/제거” 가능한 역할
