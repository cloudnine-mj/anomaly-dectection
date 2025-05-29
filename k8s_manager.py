from kubernetes import client, config, utils
from kubernetes.client.rest import ApiException
import yaml
import logging
import os

# 로깅 Configure
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class K8sManager:
    def __init__(self, kubeconfig: str = None, in_cluster: bool = True):
        if in_cluster:
            config.load_incluster_config()
            logging.info("Loaded in-cluster Kubernetes configuration")
        else:
            kubeconfig_path = kubeconfig or os.getenv('KUBECONFIG')
            config.load_kube_config(config_file=kubeconfig_path)
            logging.info(f"Loaded kubeconfig from {kubeconfig_path}")
        self.batch_v1 = client.BatchV1beta1Api()
        self.core_v1 = client.CoreV1Api()

    def create_or_update_cronjob(self, namespace: str, manifest_path: str):
        with open(manifest_path) as f:
            cronjob_manifest = yaml.safe_load(f)
        name = cronjob_manifest['metadata']['name']

        try:
            existing = self.batch_v1.read_namespaced_cron_job(name, namespace)
            # CronJob exists, patch it
            logging.info(f"Patching existing CronJob: {name}")
            self.batch_v1.patch_namespaced_cron_job(name, namespace, cronjob_manifest)
        except ApiException as e:
            if e.status == 404:
                logging.info(f"Creating CronJob: {name}")
                self.batch_v1.create_namespaced_cron_job(namespace, cronjob_manifest)
            else:
                logging.error(f"Failed to create or patch CronJob: {e}")
                raise

    def delete_cronjob(self, name: str, namespace: str):
        try:
            self.batch_v1.delete_namespaced_cron_job(name, namespace)
            logging.info(f"Deleted CronJob: {name}")
        except ApiException as e:
            if e.status == 404:
                logging.warning(f"CronJob {name} not found in {namespace}")
            else:
                logging.error(f"Error deleting CronJob: {e}")
                raise

    def create_or_update_configmap(self, namespace: str, name: str, data: dict):
        body = client.V1ConfigMap(metadata=client.V1ObjectMeta(name=name), data=data)
        try:
            existing = self.core_v1.read_namespaced_config_map(name, namespace)
            logging.info(f"Patching ConfigMap: {name}")
            self.core_v1.patch_namespaced_config_map(name, namespace, body)
        except ApiException as e:
            if e.status == 404:
                logging.info(f"Creating ConfigMap: {name}")
                self.core_v1.create_namespaced_config_map(namespace, body)
            else:
                logging.error(f"Failed to create or patch ConfigMap: {e}")
                raise

    def create_or_update_secret(self, namespace: str, name: str, data: dict):
        body = client.V1Secret(metadata=client.V1ObjectMeta(name=name), data=data)
        try:
            existing = self.core_v1.read_namespaced_secret(name, namespace)
            logging.info(f"Patching Secret: {name}")
            self.core_v1.patch_namespaced_secret(name, namespace, body)
        except ApiException as e:
            if e.status == 404:
                logging.info(f"Creating Secret: {name}")
                self.core_v1.create_namespaced_secret(namespace, body)
            else:
                logging.error(f"Failed to create or patch Secret: {e}")
                raise

def main():
    manager = K8sManager(in_cluster=False)
    # Apply CronJob manifest
    manager.create_or_update_cronjob(
        namespace="compliance",
        manifest_path="k8s/employee-risk-anomaly-cronjob.yaml"
    )
    # Optionally update configmap
    manager.create_or_update_configmap(
        namespace="compliance",
        name="anomaly-config",
        data={"config.yaml": open("config.yaml").read()}
    )

if __name__ == '__main__':
    main()
