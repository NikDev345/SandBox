from app.models.yaml import *
import yaml, re
from typing import Any
from app.services.yaml_generator.utils import Utils
from app.services.tool_service import ToolService
from app.services.tool_executor import ExecutionService
from sqlalchemy.orm import Session

class YAMLGen:
    
    generator_map = {
        ResourceKind.DEPLOYMENT: Utils._generate_deployment,
        ResourceKind.SERVICE: Utils._generate_service,
        ResourceKind.CONFIGMAP: Utils._generate_configmap,
        ResourceKind.SECRET: Utils._generate_secret,
        ResourceKind.PVC: Utils._generate_pvc,
        ResourceKind.INGRESS: Utils._generate_ingress,
        ResourceKind.HPA: Utils._generate_hpa,
    }
    
    @staticmethod
    def _process_input(request: KubernetesFormRequest | KubernetesComposeRequest,
                       compose_data: dict[str, Any] | None = None):
        if isinstance(request, KubernetesFormRequest):
            return {
                "namespace": request.namespace,
                "output_format": request.output_format,
                "applications": [
                    {
                        "app_name": request.app_name,
                        "image": request.image,
                        "replicas": request.replicas,
                        "ports": request.ports,
                        "image_pull_policy": request.image_pull_policy,
                        "service_type": request.service_type,
                        "env": request.env,
                        "secrets": request.secrets,
                        "storage": request.storage,
                        "resources": request.resources,
                        "ingress": request.ingress,
                        "hpa": request.hpa,
                        "readiness_probe": request.readiness_probe,
                        "liveness_probe": request.liveness_probe,
                    }
                ]
            }
            
        # Docker compose file preprocessing
        elif isinstance(request, KubernetesComposeRequest):
            if compose_data is None:
                raise ValueError(
                    "compose data is required for KubernetesComposeRequest"
                )
                
            applications = []
            
            services = {}

            # handle multi-document YAML
            for doc in compose_data:
                if isinstance(doc, dict) and "services" in doc:
                    services.update(doc["services"])
            
            for service_name, service in services.items():
                
                # PORTS
                ports = []
                
                for port in service.get("ports", []):
                    if isinstance(port, str):
                        parts = port.split(':')
                        if len(parts) == 1:
                            host_port = container_port = int(parts[0])
                            
                        else:
                            host_port = int(parts[-2])
                            container_port = int(parts[-1])
                            
                        ports.append(
                            PortConfig(
                                container_port=container_port,
                                service_port=host_port,
                                protocol=Protocol.TCP,
                            )
                        )
                        
                    elif isinstance(port, dict):
                        ports.append(
                            PortConfig(
                                container_port=port.get("target"),
                                service_port=port.get("published", port.get("target")),
                                protocol=Protocol(
                                    port.get("protocol", "TCP").upper()
                                ),
                            )
                        )
                        
                # ENVIRONMENT
                env = []
                
                environment = service.get("environment", {})
                
                if isinstance(environment, dict):
                    for key, value in environment.items():
                        env.append(
                            EnvVariable(
                                key=key,
                                value=str(value),
                            )
                        )
                        
                elif isinstance(environment, list):
                    for item in environment:
                        if "=" in item:
                            key, value = item.split("=")
                            
                            env.append(
                                EnvVariable(
                                    key=key,
                                    value=value,
                                )
                            )
                            
                # Storage
                
                storage = None
                
                volumes = service.get("volumes", [])
                
                if volumes:
                    first_volume = volumes[0]
                    
                    if isinstance(first_volume, str):
                        parts = first_volume.split(":")
                        if len(parts) >= 2:
                            storage = StorageConfig(
                                enabled=True,
                                pvc_name=parts[0].replace("_", "-"),
                                mount_path=parts[1],
                                storage_size="1Gi",
                            )
                            
                applications.append({
                        "app_name": service_name,
                        "image": service.get("image"),
                        "replicas": 1,
                        "ports": ports,
                        "image_pull_policy": ImagePullPolicy.IF_NOT_PRESENT,
                        "service_type": request.override_service_type,
                        "env": env,
                        "secrets": [],
                        "storage": storage,
                        "resources": None,
                        "ingress": (
                            IngressConfig(enabled=True, host=f"{service_name}.example.com", path="/",)
                            if request.enable_ingress
                            else None
                        ),
                        "hpa": (
                            HPAConfig(enabled=True)
                            if request.enable_hpa
                            else None
                        ),
                    }
                )
                
            return {
                "namespace": request.namespace,
                "output_format": request.output_format,
                "applications": applications,
            }
            
        else:
            raise TypeError(
                "Unsupported request type."
            )
            
    @staticmethod
    def _validate_request(normalized: dict) -> None:
        app_names = set()

        for app in normalized["applications"]:

            # -------------------------------------------------
            # Application Name
            # -------------------------------------------------

            app_name = app["app_name"].strip()

            if not app_name:
                raise ValueError("Application name cannot be empty.")

            if app_name in app_names:
                raise ValueError(
                    f"Duplicate application name '{app_name}'."
                )

            app_names.add(app_name)

            # -------------------------------------------------
            # Image
            # -------------------------------------------------

            if not app["image"]:
                raise ValueError(
                    f"Application '{app_name}' must have an image."
                )

            # -------------------------------------------------
            # Replicas
            # -------------------------------------------------

            if app["replicas"] < 1:
                raise ValueError(
                    f"Application '{app_name}' replicas must be at least 1."
                )

            # -------------------------------------------------
            # Ports
            # -------------------------------------------------

            used_container_ports = set()
            used_service_ports = set()

            for port in app["ports"]:

                if not (1 <= port.container_port <= 65535):
                    raise ValueError(
                        f"Invalid container port {port.container_port} in '{app_name}'."
                    )

                if not (1 <= port.service_port <= 65535):
                    raise ValueError(
                        f"Invalid service port {port.service_port} in '{app_name}'."
                    )

                if port.container_port in used_container_ports:
                    raise ValueError(
                        f"Duplicate container port {port.container_port} in '{app_name}'."
                    )

                if port.service_port in used_service_ports:
                    raise ValueError(
                        f"Duplicate service port {port.service_port} in '{app_name}'."
                    )

                used_container_ports.add(port.container_port)
                used_service_ports.add(port.service_port)

            # -------------------------------------------------
            # Environment Variables
            # -------------------------------------------------

            env_keys = set()

            for env in app["env"]:

                if env.key in env_keys:
                    raise ValueError(
                        f"Duplicate environment variable '{env.key}' in '{app_name}'."
                    )

                env_keys.add(env.key)

            # -------------------------------------------------
            # Secrets
            # -------------------------------------------------

            secret_keys = set()

            for secret in app["secrets"]:

                if secret.key in secret_keys:
                    raise ValueError(
                        f"Duplicate secret '{secret.key}' in '{app_name}'."
                    )

                secret_keys.add(secret.key)

            # -------------------------------------------------
            # Duplicate Env & Secret Keys
            # -------------------------------------------------

            duplicate = env_keys.intersection(secret_keys)

            if duplicate:
                raise ValueError(
                    f"Variables cannot exist in both env and secrets: "
                    f"{', '.join(sorted(duplicate))}"
                )

            # -------------------------------------------------
            # Storage
            # -------------------------------------------------

            storage = app.get("storage")

            if storage and storage.enabled:

                if not storage.pvc_name:
                    raise ValueError(
                        f"PVC name missing in '{app_name}'."
                    )

                if storage.storage_size and not re.fullmatch(
                    r"\d+(Mi|Gi|Ti)",
                    storage.storage_size,
                ):
                    raise ValueError(
                        f"Invalid storage size '{storage.storage_size}' in '{app_name}'."
                    )

                if not storage.mount_path:
                    raise ValueError(
                        f"Mount path missing in '{app_name}'."
                    )

                if not re.fullmatch(
                    r"\d+(Mi|Gi|Ti)",
                    storage.storage_size,
                ):
                    raise ValueError(
                        f"Invalid storage size '{storage.storage_size}' in '{app_name}'."
                    )

            # -------------------------------------------------
            # Ingress
            # -------------------------------------------------

            ingress = app.get("ingress")

            if ingress and ingress.enabled:

                if not app["ports"]:
                    raise ValueError(
                        f"Ingress requires at least one service port in '{app_name}'."
                    )

            # -------------------------------------------------
            # HPA
            # -------------------------------------------------

            hpa = app.get("hpa")

            if hpa and hpa.enabled:

                if hpa.min_replicas < 1:
                    raise ValueError(
                        f"Minimum replicas must be at least 1 in '{app_name}'."
                    )

                if hpa.max_replicas < hpa.min_replicas:
                    raise ValueError(
                        f"Maximum replicas must be greater than or equal to minimum replicas in '{app_name}'."
                    )

                if not (
                    1 <= hpa.target_cpu_utilization_percentage <= 100
                ):
                    raise ValueError(
                        f"CPU utilization must be between 1 and 100 in '{app_name}'."
                    )
            
    @staticmethod
    def _build_resource_plan(normalized_input: dict) -> dict:

        plan = {
            "namespace": normalized_input["namespace"],
            "output_format": normalized_input["output_format"],
            "applications": [],
        }

        for app in normalized_input["applications"]:

            resources = []

            # Deployment is always required
            resources.append(ResourceKind.DEPLOYMENT)

            # Service
            if app.get("ports"):
                resources.append(ResourceKind.SERVICE)

            # ConfigMap
            if app.get("env"):
                resources.append(ResourceKind.CONFIGMAP)

            # Secret
            if app.get("secrets"):
                resources.append(ResourceKind.SECRET)

            # Persistent Volume Claim
            storage = app.get("storage")
            if storage and storage.enabled:
                resources.append(ResourceKind.PVC)

            # Ingress
            ingress = app.get("ingress")
            if ingress and ingress.enabled:
                resources.append(ResourceKind.INGRESS)

            # Horizontal Pod Autoscaler
            hpa = app.get("hpa")
            if hpa and hpa.enabled:
                resources.append(ResourceKind.HPA)

            plan["applications"].append(
                {
                    "config": app,
                    "resources": resources,
                }
            )

        return plan
    
    @staticmethod
    def _generate_resources(plan: dict):
        
        generated = {
            "namespace": plan["namespace"],
            "output_format": plan["output_format"],
            "generated": [],
        }
        
        for application in plan["applications"]:
            app_config = application["config"]
            resource_objects = {}
            
            for resource in application["resources"]:
                generator = YAMLGen.generator_map[resource]
                resource_objects[resource] = generator(app_config)
                
            generated['generated'].append(
                {
                "app_name": app_config["app_name"],
                "resources": resource_objects
                }
            )
            
        return generated
    
    @staticmethod
    def _resource_filename(app_name: str, resource: ResourceKind) -> str:

        names = {
            ResourceKind.DEPLOYMENT: "deployment",
            ResourceKind.SERVICE: "service",
            ResourceKind.CONFIGMAP: "configmap",
            ResourceKind.SECRET: "secret",
            ResourceKind.PVC: "pvc",
            ResourceKind.INGRESS: "ingress",
            ResourceKind.HPA: "hpa",
        }

        return f"{app_name}-{names[resource]}.yaml"
        
    @staticmethod
    def _render_yaml_files(generated_resources: dict) -> list[GeneratedFile]:
        files = []
        
        output_format = generated_resources["output_format"]
        
        # MULTIPLE FILES FORMAT
        if output_format == OutputFormat.MULTIPLE:
            
            for application in generated_resources["generated"]:
                app_name = application["app_name"]
                
                for resource_kind, manifest in application["resources"].items():
                    yaml_content = yaml.safe_dump(
                        manifest,
                        sort_keys=False,
                        default_flow_style=False
                    )
                    
                    files.append(
                        GeneratedFile(
                            filename=YAMLGen._resource_filename(app_name, resource_kind),
                            content=yaml_content,
                            size=len(yaml_content.encode("utf-8")),
                        )
                    )
                    
            return files
        
        # SINGLE FILE FORMAT
        
        manifests = []
        resources = []
        
        for application in generated_resources["generated"]:
            for resource_kind, manifest in application["resources"].items():
                
                manifests.append(
                    yaml.safe_dump(
                        manifest,
                        sort_keys=False,
                        default_flow_style=False,
                    )
                )
                
                resources.append(resource_kind)
        combined_yaml = "---\n".join(manifests)
        files.append(
            GeneratedFile(
                filename="kubernetes.yaml",
                content="---\n".join(manifests),
                size=len(combined_yaml.encode("utf-8")),
            )
        )
        
        return files
            
    @staticmethod
    def _build_summary(plan: dict, files: list[GeneratedFile]):
        resources = []
        seen = set()
        
        for application in plan["applications"]:
            for resource in application["resources"]:
                if resource not in seen:
                    seen.add(resource)
                    resources.append(resource)
                    
        summary = (
            f"Successfully generated {len(files)} Kubernetes manifest(s) "
            f"for {len(plan['applications'])} application(s) in the "
            f'"{plan["namespace"]}" namespace.'
        )
        
        return GenerationSummary(
            namespace=plan["namespace"],
            resources_generated=resources,
            validation_passed=True,
            summary=summary,
        )
        
    @staticmethod
    def generate(
        request: KubernetesFormRequest | KubernetesComposeRequest,
        user_id: str,
        db: Session,
        compose_data: dict | None = None,
    ) -> KubernetesGeneratorResponse:

        # Step 1: Normalize input
        normalized = YAMLGen._process_input(
            request=request,
            compose_data=compose_data,
        )
        
        YAMLGen._validate_request(normalized)

        # Step 2: Determine required resources
        plan = YAMLGen._build_resource_plan(normalized)

        # Step 3: Generate Kubernetes manifests
        generated = YAMLGen._generate_resources(plan)

        # Step 4: Render manifests to YAML files
        files = YAMLGen._render_yaml_files(generated)

        # Step 5: Build response summary
        summary = YAMLGen._build_summary(
            plan=plan,
            files=files,
        )

        # Step 6: Build generated resources list
        resources = []

        for application in generated["generated"]:

            app_name = application["app_name"]

            for resource_kind in application["resources"]:

                resources.append(
                    GeneratedResource(
                        kind=resource_kind,
                        name=app_name,
                        filename=YAMLGen._resource_filename(
                            app_name,
                            resource_kind,
                        ),
                    )
                )
                
            
        res = KubernetesGeneratorResponse(
            summary=summary,
            resources=resources,
            files=files,
        ).model_dump_json()
                
        tool = ToolService.get_tool_by_slug(
                db=db,
                slug="yaml_generator",
            )
        tool_id = tool.id if tool else "yaml_generator"
        execution_id: Optional[str] = None
        try:
            execution = ExecutionService.create_execution(
                db=db,
                user_id=user_id,
                tool_id=tool_id,
                user_input=request.model_dump_json(),
                output=res,
            )
            execution_id = execution.id
        except Exception:
            pass

        # Step 7: Return response
        response = KubernetesGeneratorResponse(
            summary=summary,
            resources=resources,
            files=files,
            execution_id=execution_id,
        )
        return response