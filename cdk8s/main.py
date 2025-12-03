#!/usr/bin/env python
from constructs import Construct
from cdk8s import App, Chart

from imports.k8s import (
    KubeDeployment,
    DeploymentSpec,
    LabelSelector,
    PodTemplateSpec,
    ObjectMeta,
    PodSpec,
    Container,
    ContainerPort,
    KubeService,
    ServiceSpec,
    ServicePort,
    IntOrString,
)

class MyChart(Chart):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # define resources here
        label = {"app": "hello-k8s"}

        KubeDeployment(self, 'deployment',
                           spec=DeploymentSpec(
                               replicas=2,
                               selector=LabelSelector(match_labels=label),
                               template=PodTemplateSpec(
                                   metadata=ObjectMeta(labels=label),
                                   spec=PodSpec(containers=[
                                       Container(
                                           name='hello-kubernetes',
                                           image='paulbouwer/hello-kubernetes:1.7',
                                           ports=[ContainerPort(container_port=8080)])]))))

        KubeService(self, 'service',
                        spec=ServiceSpec(
                            type='LoadBalancer',
                            ports=[ServicePort(port=80, target_port=IntOrString.from_number(8080))],
                            selector=label))


app = App()
MyChart(app, "cdk8s")

app.synth()
