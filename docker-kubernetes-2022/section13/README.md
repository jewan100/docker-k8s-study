# Kubernetes Storage

애플리케이션 설계 기본 원칙

- 애플리케이션은 최대한 Stateless 아키텍처 지향
- 상태 데이터는 데이터베이스, 외부 스토리지, 메시지 큐 등에 위임함
- 그럼에도 불구하고 파일 시스템이 필요한 경우에 사용하는 것이 Kubernetes Storage, 특히 PersistentVolume 구조

## Volumes

Volumes [https://kubernetes.io/ko/docs/concepts/storage/volumes/](https://kubernetes.io/ko/docs/concepts/storage/volumes/)

기본 개념

- Volume은 Pod 스펙 내부에 정의되는 스토리지 리소스
- Volume의 라이프사이클은 기본적으로 Pod 수명에 종속됨

  - Volume 정의 자체는 Pod 스펙의 일부
  - Pod가 삭제되면 emptyDir와 같은 일시적 볼륨은 함께 삭제됨

- Kubernetes Volume 개념은 Docker Volume과는 별도 개념

  - Kubernetes는 다양한 스토리지 드라이버와 타입을 추상화하는 구조

- “볼륨이 영구적이다 / 아니다”는 타입에 따라 다름

  - `emptyDir`, `hostPath` 등은 Pod 또는 노드 수명에 묶이는 경향
  - `PersistentVolume` + `PersistentVolumeClaim` 조합은 클러스터 리소스로서 보다 안정적인 수명 보장

“쿠버네티스의 볼륨은 어디에 있나?”라는 관점

- `emptyDir` Pod가 스케줄된 노드의 임시 디스크 영역
- `hostPath` 노드(가상머신 혹은 물리 서버)의 실제 파일 시스템 경로
- 클라우드 스토리지(CSI 드라이버 사용 시) 클라우드 블록 스토리지나 NFS, 파일 스토리지 등에 매핑
- 요약 Kubernetes는 “어디에 있든지 간에” 이를 Pod 입장에서 통일된 Volume 인터페이스로 제공하는 추상화 계층

## Volume 사용 예시

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: story-deployment
spec:
  replicas: 2 # 유지할 Pod 개수(레플리카 수)
  selector:
    matchLabels:
      app: story
  template:
    metadata:
      labels:
        app: story
    spec:
      containers:
        - name: story
          image: jewan100/kub-data-demo:1
          env:
            - name: STORY_FOLDER # 애플리케이션에서 사용할 폴더 경로
              valueFrom:
                configMapKeyRef: # ConfigMap에서 환경 변수 값 참조
                  name: data-story-env
                  key: folder
          volumeMounts:
            - mountPath: /app/story # 컨테이너 내부에서 볼륨이 마운트되는 경로
              name: story-volume # 아래 volumes 섹션의 볼륨 이름과 일치
      volumes:
        - name: story-volume
          # emptyDir: {} # 볼륨 타입(emptyDir), 같은 Pod 내 컨테이너끼리 공유, Pod 간 공유 불가

          # hostPath: # 볼륨 타입(hostPath), 같은 노드에 스케줄된 Pod끼리만 실질적으로 공유 가능
          #   path: /data # 노드(호스트)의 실제 디렉터리 경로
          #   type: DirectoryOrCreate # 디렉터리가 없으면 자동 생성

          persistentVolumeClaim: # 볼륨 타입(PersistentVolumeClaim), PVC가 바인딩한 PV를 Pod에 연결
            claimName: host-pvc # 사용할 PersistentVolumeClaim 이름
```

여기서 `volumes` 아래에 어떤 타입을 쓰느냐에 따라 동작이 달라짐

### emptyDir

특징

- Pod가 생성될 때 노드의 임시 디렉터리를 하나 할당하는 타입
- 같은 Pod 안에 있는 모든 컨테이너가 해당 emptyDir를 공유함
- Pod가 삭제되면(emptyDir를 사용하는 컨테이너가 모두 종료되면) 데이터도 함께 삭제됨

주의 사항

- Pod가 Scaling Out되어 새 Pod가 다른 노드에 생성되면

  - 기존 Pod의 emptyDir 데이터는 새로운 Pod에서 접근 불가

- “Pod 내부 컨테이너 간 임시 파일 공유”에 적합한 타입

### hostPath

특징

- 노드(호스트)의 특정 디렉터리를 그대로 Pod에 마운트하는 타입
- 같은 노드에 스케줄된 여러 Pod가 같은 hostPath를 마운트하면 데이터 공유 가능

주의 사항

- 노드에 종속된 스토리지 구조

  - Pod가 다른 노드로 스케줄되면 동일한 path라도 물리 디스크가 다름

- minikube 같은 단일 노드 환경에서는 “호스트 = minikube VM”의 디스크 경로와 연결
- 다중 노드 프로덕션 환경에서는 hostPath는 되도록 피하고, PV/PVC 또는 클라우드 스토리지 사용이 일반적인 패턴

### CSI (Container Storage Interface)

- 다양한 스토리지 벤더가 Kubernetes에 스토리지를 붙일 수 있게 해주는 표준 인터페이스
- NFS, 클라우드 블록 스토리지, 분산 파일 시스템 등 다양한 구현체 존재
- 실제 YAML에서는 `csi` 볼륨 타입 또는 특정 StorageClass를 통해 사용하게 되는 구조

## Persistent Volumes

일반 Pod 스펙 내부의 `volumes`와 차이점

- `PersistentVolume(PV)`는 클러스터 레벨의 독립 리소스

  - 특정 Pod 정의와 분리된 “스토리지 풀” 같은 개념
  - 노드, Pod 라이프사이클과 분리된 관리 단위

- Pod는 직접 PV를 참조하지 않고, `PersistentVolumeClaim(PVC)`를 통해 간접적으로 PV를 사용

예시

```yaml
apiVersion: v1
kind: PersistentVolume # PersistentVolume 리소스 정의
metadata:
  name: host-pv
spec:
  capacity:
    storage: 1Gi # 제공할 저장 용량
  volumeMode: Filesystem # 볼륨 모드(Filesystem 또는 Block)
  storageClassName: standard # 스토리지 클래스 이름(PVC와 매칭될 값)
  accessModes:
    - ReadWriteOnce # 접근 모드(ReadWriteOnce, ReadOnlyMany, ReadWriteMany) 중 하나, 단일 노드에서 읽기/쓰기 허용
  hostPath:
    path: /data # 노드(호스트)의 실제 디렉터리 경로
    type: DirectoryOrCreate # 디렉터리가 없으면 자동 생성
```

- PV는 “이 클러스터에 1Gi 용량의 /data 스토리지가 있다”라는 선언
- `accessModes`, `storageClassName` 등 특성을 통해 어떤 PVC와 매칭 가능한지 결정함

## Persistent Volume Claim

> “이 정도 성격, 이 정도 용량의 스토리지를 쓰고 싶다”라는 Pod 측의 요청 리소스

PVC는 PV를 소비하기 위한 Claim 리소스

```yaml
apiVersion: v1
kind: PersistentVolumeClaim # PersistentVolumeClaim 리소스 정의
metadata:
  name: host-pvc
spec:
  volumeName: host-pv # 바인딩할 PersistentVolume 이름(정적 바인딩)
  accessModes:
    - ReadWriteOnce # PV와 동일한 접근 모드 요청
  storageClassName: standard # 매칭될 스토리지 클래스 이름
  resources:
    requests:
      storage: 1Gi # 요청할 최소 저장 용량
```

동작 흐름

- PVC가 생성되면 Kubernetes가 조건에 맞는 PV를 찾아 바인딩

  - `volumeName`을 지정하면 해당 PV와 직접 연결되는 정적 바인딩
  - 일반적으로는 `storageClassName`, `accessModes`, `requests.storage` 기준으로 자동 매칭되는 패턴

- Pod는 `volumes.persistentVolumeClaim.claimName: host-pvc` 형태로 PVC를 참조

  - 실제 물리 스토리지(PV)는 Pod 입장에서 숨겨진 추상화 계층

## StorageClass

> “PV를 어떻게 생성할 것인지”에 대한 템플릿 및 정책 정의 리소스

개념

- StorageClass는 스토리지 관리 방식을 캡슐화하는 구성 단위
- 관리자는 StorageClass를 통해

  - 어떤 스토리지 백엔드를 사용할지
  - 어떤 파라미터(디스크 타입, IOPS 등)로 동적 프로비저닝할지
    를 정의함

연결 관계

- PVC에서 `storageClassName: standard` 를 지정하면

  - 해당 StorageClass 정책에 따라 PV가 동적으로 생성되는 구조

- 지금 작성한 예시는 `volumeName`으로 특정 PV를 직접 참조하는 정적 바인딩 예시이므로

  - 동적 프로비저닝보다는 개념 이해용으로 적합한 패턴

## 환경 변수 설정과 ConfigMap

볼륨과 직접적인 스토리지 리소스는 아니지만, 볼륨 경로를 환경 변수로 관리하면 설정 관리가 편해짐

ConfigMap 예시

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: data-story-env
data:
  # key: value 형태의 설정 데이터 정의
  folder: story # STORY_FOLDER 환경 변수로 주입할 폴더 이름
```

Deployment에서 참조

```yaml
env:
  - name: STORY_FOLDER
    valueFrom:
      configMapKeyRef:
        name: data-story-env
        key: folder
```

이렇게 하면

- 코드 상에서는 `STORY_FOLDER` 환경 변수를 참조
- 실제 폴더 이름 변경이 필요할 때는 ConfigMap만 수정해 재배포하면 되는 구조
