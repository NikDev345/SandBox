from enum import Enum
from pydantic import Field, BaseModel
from typing import List, Optional

class InputMode(str, Enum):
    FORM = "form"
    COMPOSE = "compose"


class OutputFormat(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"


class ServiceType(str, Enum):
    CLUSTER_IP = "ClusterIP"
    NODE_PORT = "NodePort"
    LOAD_BALANCER = "LoadBalancer"


class Protocol(str, Enum):
    TCP = "TCP"
    UDP = "UDP"


class ImagePullPolicy(str, Enum):
    ALWAYS = "Always"
    IF_NOT_PRESENT = "IfNotPresent"
    NEVER = "Never"


class AccessMode(str, Enum):
    READ_WRITE_ONCE = "ReadWriteOnce"
    READ_ONLY_MANY = "ReadOnlyMany"
    READ_WRITE_MANY = "ReadWriteMany"


class ResourceKind(str, Enum):
    DEPLOYMENT = "Deployment"
    SERVICE = "Service"
    CONFIGMAP = "ConfigMap"
    SECRET = "Secret"
    PVC = "PersistentVolumeClaim"
    INGRESS = "Ingress"
    HPA = "HorizontalPodAutoscaler"
    
class GeneratedResource(BaseModel):
    kind: ResourceKind
    name: str
    filename: str
    
class EnvVariable(BaseModel):
    key: str
    value: str
    
class SecretVariable(BaseModel):
    key: str
    value: str
    
class PortConfig(BaseModel):
    container_port: int
    service_port: int
    protocol: Protocol = Protocol.TCP
    
class ResourceConfig(BaseModel):
    cpu_request: Optional[str] = None
    cpu_limit: Optional[str] = None
    memory_request: Optional[str] = None
    memory_limit: Optional[str] = None
    
class StorageConfig(BaseModel):
    enabled: bool = False
    pvc_name: Optional[str] = None
    storage_size: Optional[str] = None
    mount_path: Optional[str] = None
    access_mode: AccessMode = AccessMode.READ_WRITE_ONCE
    
class ProbeConfig(BaseModel):
    enabled: bool = False
    path: Optional[str] = None
    port: Optional[int] = None
    initial_delay_seconds: int = 10
    period_seconds: int = 10
    
class HPAConfig(BaseModel):
    enabled: bool = False
    min_replicas: int = 1
    max_replicas: int = 5
    target_cpu_utilization_percentage: int = 80
    
class IngressConfig(BaseModel):
    enabled: bool = False
    host: Optional[str] = None
    path: str = "/"
    tls_enabled: bool = False
    
class KubernetesFormRequest(BaseModel):
    app_name: str
    namespace: str = "default"

    image: str
    image_pull_policy: ImagePullPolicy = ImagePullPolicy.IF_NOT_PRESENT

    replicas: int = 1

    ports: List[PortConfig]

    service_type: ServiceType = ServiceType.CLUSTER_IP

    env: List[EnvVariable] = Field(default_factory=list)
    secrets: List[SecretVariable] = Field(default_factory=list)

    resources: ResourceConfig = Field(default_factory=ResourceConfig)

    storage: Optional[StorageConfig] = None

    readiness_probe: Optional[ProbeConfig] = None

    liveness_probe: Optional[ProbeConfig] = None

    ingress: Optional[IngressConfig] = None

    hpa: Optional[HPAConfig] = None

    output_format: OutputFormat = OutputFormat.MULTIPLE
    
class KubernetesComposeRequest(BaseModel):
    namespace: str = "default"

    output_format: OutputFormat = OutputFormat.MULTIPLE

    override_service_type: ServiceType = ServiceType.CLUSTER_IP

    enable_ingress: bool = False

    enable_hpa: bool = False
    
class GeneratedFile(BaseModel):
    filename: str
    content: str
    size: int
    
class GenerationSummary(BaseModel):
    namespace: str

    resources_generated: List[ResourceKind]

    validation_passed: bool
    
    summary: str

    
class KubernetesGeneratorResponse(BaseModel):
    summary: GenerationSummary
    resources: List[GeneratedResource]
    files: List[GeneratedFile]
    execution_id: Optional[str] = None
    
class ValidationIssue(BaseModel):
    field: str
    message: str

class KubernetesGeneratorError(BaseModel):
    success: bool = False

    errors: List[ValidationIssue]