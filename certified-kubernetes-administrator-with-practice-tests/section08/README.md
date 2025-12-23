# Kubernetes Storage

## Volumes

> Pod 스펙 안에서 바로 정의하는 “일회성” 스토리지 추상화

- 볼륨 자체는 항상 Pod 단위 라이프사이클

  - Pod가 삭제되면 해당 볼륨(특히 emptyDir 등)도 함께 사라짐

- `spec.volumes` 에서 볼륨을 정의하고,
  `containers[].volumeMounts` 에서 컨테이너 안에 마운트하는 방식
- 타입에 따라 실제 백엔드가 다름

  - `emptyDir`, `hostPath`, `configMap`, `secret`, `persistentVolumeClaim`, `csi` 등

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-pod
spec:
  containers:
    - name: test
      image: busybox:1.28
      command: ["sh", "-c", 'echo "The app is running!" && tail -f /dev/null']
      volumeMounts:
        - name: config-vol
          mountPath: /etc/config # 컨테이너 내부에서 /etc/config 경로로 마운트
  volumes:
    - name: config-vol
      configMap:
        name: log-config # ConfigMap 리소스 이름
        items:
          - key: log_level # ConfigMap의 key
            path: log_level.conf # 컨테이너 내부 파일 이름
```

- `volumes.configMap`

  - `log-config` ConfigMap의 데이터를 파일 형태로 볼륨에 투영
  - `log_level` 키 → `/etc/config/log_level.conf` 로 파일 생성

- 주의점

  - ConfigMap 자체는 etcd에 저장되지만, Pod 안에서는 단순 파일 로 보임
  - Pod 삭제 시 마운트된 볼륨도 같이 사라지고, 다시 생성되면 ConfigMap 내용 기준으로 재생성

## Persistent Volumes (PV)

> “Pod에 종속되지 않는” 클러스터 레벨의 스토리지 리소스

- 관리자가 미리 만들어두거나(StorageClass 없이 정적 프로비저닝)
  StorageClass를 통해 필요할 때 자동으로 만들어지는(동적 프로비저닝) 스토리지 조각
- 각 PV는 용량, 접근 모드, 스토리지 타입 등의 스펙을 가짐
- PV는 클러스터 리소스이고, Pod에 직접 연결되지 않고, PersistentVolumeClaim(PVC) 를 통해 간접적으로 연결

접근 모드(accessModes)

- `ReadWriteOnce (RWO)`

  - 한 노드에서만 읽기/쓰기 마운트 가능
  - (단, 같은 노드 내 여러 Pod가 같은 PVC를 공유하는 것은 스토리지 종류에 따라 가능)

- `ReadOnlyMany (ROX)`

  - 여러 노드에서 읽기 전용 마운트 가능

- `ReadWriteMany (RWX)`

  - 여러 노드에서 읽기/쓰기 동시 마운트 가능
  - NFS, 일부 클라우드 파일 스토리지 등에서 지원

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: example-pv
spec:
  capacity:
    storage: 10Gi # 제공 가능한 용량
  volumeMode: Filesystem # Filesystem 또는 Block
  accessModes:
    - ReadWriteOnce
  storageClassName: slow # StorageClass와 매칭되는 이름
  persistentVolumeReclaimPolicy: Retain # Delete, Retain, Recycle(구버전)
  hostPath:
    path: /data/pv1 # 예시용 hostPath (실운영에서는 NFS, EBS, Ceph 등 사용)
```

## Persistent Volume Claims (PVC)

> 애플리케이션(네임스페이스 측)에서 “이 정도 스펙의 스토리지가 필요하다” 라고 요청하는 객체

- PV와의 관계는 논리적으로 1:1 바인딩

  - 한 PVC는 하나의 PV에만 바인딩
  - 바인딩 이후에는 다른 PV로 자동 이동하지 않음 (삭제 후 재요청 등 필요)

- 여러 Pod에서 같은 PVC를 참조하면, 결과적으로 같은 PV를 공유하는 구조

  - 이때 동시에 마운트 가능한지 여부는 PV의 `accessModes` 및 실제 스토리지 백엔드가 결정

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: myclaim
spec:
  accessModes:
    - ReadWriteOnce # 이 PVC가 요청하는 접근 모드
  volumeMode: Filesystem
  resources:
    requests:
      storage: 8Gi # 필요한 용량
  storageClassName: slow # 이 StorageClass에서 제공하는 PV를 요청
  selector: # 특정 라벨을 가진 PV만 매칭
    matchLabels:
      release: "stable"
    matchExpressions:
      - key: environment
        operator: In
        values: [dev]
```

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-using-pvc
spec:
  containers:
    - name: app
      image: my/app:latest
      volumeMounts:
        - name: data
          mountPath: /app/data
  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: myclaim # 위에서 정의한 PVC 이름
```

정리

- 애플리케이션 쪽에서는 “PVC 이름만 알고 있으면 됨”
- 실제 스토리지 구현(EBS, NFS, Ceph, hostPath 등)은 PV/StorageClass 레벨에서 숨김

## StorageClass

> “어떤 방식으로, 어떤 스토리지를, 어떤 옵션으로 만들지” 를 정의하는 템플릿

- 정적 프로비저닝(PV 수동 생성)

  - 관리자가 직접 PV를 만들고 PVC가 그중 하나를 잡아서 사용
  - PV 관리 부담이 큼

- 동적 프로비저닝(StorageClass 기반 자동 생성)

  - PVC가 생성될 때 StorageClass를 참조해서, 필요한 PV를 자동 생성
  - 클라우드 디스크(EBS, PD, Azure Disk 등)나 NFS, Ceph 등을 자동 할당

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: slow
provisioner: kubernetes.io/aws-ebs # 예시: AWS EBS 프로비저너 (요즘은 csi.drivers 사용)
parameters:
  type: gp2 # EBS 타입, IOPS 등 클래스 정의
reclaimPolicy: Delete # PVC 삭제 시 PV도 함께 삭제
volumeBindingMode: WaitForFirstConsumer # 실제 Pod가 스케줄되기 전까지 물리 볼륨 생성 지연
```

- `provisioner`

  - 어떤 드라이버가 실제 스토리지를 만들지

- `parameters`

  - 스토리지 특성(디스크 타입, IOPS, 스토리지 계층 등) 지정

- `reclaimPolicy`

  - `Delete` PVC 삭제 시 PV/실제 디스크까지 삭제
  - `Retain` PVC 삭제 후 PV, 실제 데이터 유지 (수동 정리용)

- `volumeBindingMode`

  - `Immediate` PVC 생성과 동시에 실제 볼륨 프로비저닝
  - `WaitForFirstConsumer` 실제 Pod가 어떤 노드에 스케줄될지 결정된 이후 프로비저닝

1. PVC 생성 시 `storageClassName: slow` 지정
2. 컨트롤플레인이 `slow` StorageClass를 확인
3. 해당 StorageClass의 `provisioner` 가 실제 스토리지(EBS, NFS 등)를 생성하고 PV도 함께 생성
4. 자동으로 PVC ↔ PV 바인딩 완료
5. Pod에서 `persistentVolumeClaim.claimName` 으로 사용
