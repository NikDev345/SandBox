from app.models.yaml import *
import base64

class Utils:
    
    @staticmethod
    def _generate_deployment(app: dict) -> dict:

        labels = {
            "app": app["app_name"],
            "app.kubernetes.io/name": app["app_name"],
            "app.kubernetes.io/managed-by": "AI Toolbox",
        }

        container = {
            "name": app["app_name"],
            "image": app["image"],
            "imagePullPolicy": app.get(
                "image_pull_policy",
                ImagePullPolicy.IF_NOT_PRESENT,
            ).value,
        }

        # -----------------------------
        # Ports
        # -----------------------------

        if app["ports"]:

            container["ports"] = [
                {
                    "containerPort": port.container_port,
                    "protocol": port.protocol.value,
                }
                for port in app["ports"]
            ]

        # -----------------------------
        # Environment Variables
        # -----------------------------

        env = []

        # ConfigMap References
        for variable in app["env"]:

            env.append(
                {
                    "name": variable.key,
                    "valueFrom": {
                        "configMapKeyRef": {
                            "name": f"{app['app_name']}-config",
                            "key": variable.key,
                        }
                    },
                }
            )

        # Secret References
        for secret in app["secrets"]:

            env.append(
                {
                    "name": secret.key,
                    "valueFrom": {
                        "secretKeyRef": {
                            "name": f"{app['app_name']}-secret",
                            "key": secret.key,
                        }
                    },
                }
            )

        if env:
            container["env"] = env

        # -----------------------------
        # Resources
        # -----------------------------

        resources = {}

        if app["resources"]:

            requests = {}
            limits = {}

            if app["resources"].cpu_request:
                requests["cpu"] = app["resources"].cpu_request

            if app["resources"].memory_request:
                requests["memory"] = app["resources"].memory_request

            if app["resources"].cpu_limit:
                limits["cpu"] = app["resources"].cpu_limit

            if app["resources"].memory_limit:
                limits["memory"] = app["resources"].memory_limit

            if requests:
                resources["requests"] = requests

            if limits:
                resources["limits"] = limits

        if resources:
            container["resources"] = resources

        # -----------------------------
        # Readiness Probe
        # -----------------------------

        readiness = app.get("readiness_probe")

        if readiness and readiness.enabled:

            container["readinessProbe"] = {
                "httpGet": {
                    "path": readiness.path,
                    "port": readiness.port,
                },
                "initialDelaySeconds": readiness.initial_delay_seconds,
                "periodSeconds": readiness.period_seconds,
            }

        # -----------------------------
        # Liveness Probe
        # -----------------------------

        liveness = app.get("liveness_probe")

        if liveness and liveness.enabled:

            container["livenessProbe"] = {
                "httpGet": {
                    "path": liveness.path,
                    "port": liveness.port,
                },
                "initialDelaySeconds": liveness.initial_delay_seconds,
                "periodSeconds": liveness.period_seconds,
            }

        # -----------------------------
        # PVC
        # -----------------------------

        volumes = []
        volume_mounts = []

        storage = app.get("storage")

        if storage and storage.enabled:

            volumes.append(
                {
                    "name": "storage",
                    "persistentVolumeClaim": {
                        "claimName": storage.pvc_name
                    },
                }
            )

            volume_mounts.append(
                {
                    "name": storage.pvc_name,
                    "mountPath": storage.mount_path,
                }
            )

        if volume_mounts:
            container["volumeMounts"] = volume_mounts

        # -----------------------------
        # Deployment
        # -----------------------------

        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": app["app_name"],
            },
            "spec": {
                "replicas": app["replicas"],
                "revisionHistoryLimit": 10,
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxUnavailable": "25%",
                        "maxSurge": "25%",
                    },
                },
                "selector": {
                    "matchLabels": labels,
                },
                "template": {
                    "metadata": {
                        "labels": labels,
                    },
                    "spec": {
                        "terminationGracePeriodSeconds": 30,
                        "containers": [
                            container,
                        ]
                    },
                },
            },
        }

        if volumes:
            deployment["spec"]["template"]["spec"]["volumes"] = volumes

        return deployment
    
    @staticmethod
    def _generate_service(app: dict) -> dict:

        labels = {
            "app": app["app_name"],
            "app.kubernetes.io/name": app["app_name"],
            "app.kubernetes.io/managed-by": "AI Toolbox",
        }

        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": app["app_name"],
            },
            "spec": {
                "selector": labels,
                "type": app["service_type"].value,
                "ports": [],
            },
        }

        for port in app["ports"]:

            service_port = {
                "port": port.service_port,
                "targetPort": port.container_port,
                "protocol": port.protocol.value,
            }

            # Optional future support
            if (
                app["service_type"] == ServiceType.NODE_PORT
                and hasattr(port, "node_port")
                and getattr(port, "node_port", None)
            ):
                service_port["nodePort"] = port.node_port

            service["spec"]["ports"].append(service_port)

        return service
    
    @staticmethod
    def _generate_configmap(app: dict) -> dict:

        data = {}

        for env in app["env"]:
            data[env.key] = env.value

        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{app['app_name']}-config",
            },
            "data": data,
        }

    @staticmethod
    def _generate_secret(app: dict) -> dict:

        data = {}

        for secret in app["secrets"]:

            data[secret.key] = (
                base64.b64encode(secret.value.encode())
                .decode()
            )

        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": f"{app['app_name']}-secret",
            },
            "type": "Opaque",
            "data": data,
        }
        
    @staticmethod
    def _generate_pvc(app: dict) -> dict:

        storage = app["storage"]

        pvc = {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": storage.pvc_name,
            },
            "spec": {
                "accessModes": [
                    storage.access_mode.value,
                ],
                "resources": {
                    "requests": {
                        "storage": storage.storage_size,
                    }
                },
            },
        }

        return pvc
    
    @staticmethod
    def _generate_ingress(app: dict) -> dict:

        ingress = app["ingress"]

        manifest = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{app['app_name']}-ingress",
            },
            "spec": {
                "rules": [
                    {
                        "host": ingress.host,
                        "http": {
                            "paths": [
                                {
                                    "path": ingress.path,
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": app["app_name"],
                                            "port": {
                                                "number": app["ports"][0].service_port
                                            },
                                        }
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
        }

        if ingress.tls_enabled:

            manifest["spec"]["tls"] = [
                {
                    "hosts": [
                        ingress.host,
                    ],
                    "secretName": f"{app['app_name']}-tls",
                }
            ]

        return manifest
    
    @staticmethod
    def _generate_hpa(app: dict) -> dict:

        hpa = app["hpa"]

        return {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": f"{app['app_name']}-hpa",
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": app["app_name"],
                },
                "minReplicas": hpa.min_replicas,
                "maxReplicas": hpa.max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {
                                "type": "Utilization",
                                "averageUtilization": hpa.target_cpu_utilization_percentage,
                            },
                        },
                    }
                ],
            },
        }