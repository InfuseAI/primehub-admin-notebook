#!/usr/bin/env python3
import re
from command import Run
import json
namespace = 'hub'


def get_ceph_tool_pod():
    result = Run(
        'kubectl get pod -n rook -l app=rook-ceph-tools -o name').pipe('head -1')
    pod = result.output()
    pod_name = pod.split('/')[1].strip() if pod else ''

    if not pod_name:
        result = Run(
            'kubectl get pod -n rook rook-tools -o name').pipe('head -1')
        pod = result.output()
        pod_name = pod.split('/')[1].strip() if pod else ''
    return pod_name


def get_ceph_image():
    ceph_tool_pod = get_ceph_tool_pod()
    result = Run(
        "kubectl get pod -n rook {} -o jsonpath={{.spec.containers[0].image}}".format(ceph_tool_pod))
    image = result.output()
    return image


def kubectl_rbd_cmd():
    ceph_tool = get_ceph_tool_pod()
    return 'kubectl exec {} -n rook -- rbd'.format(ceph_tool)


def get_hostname():
    """
    we plan use filesytem tools in the osd-pods, so we need a mapping table
    between osd-pod ---> hostIP <--- k8s node
    """
    hostnames = {}
    addresses = Run(
        "kubectl get node -o json").pipe("jq [.items[].status.addresses]").json()
    for address_types in addresses:
        # address_types would look like:
        # [{'address': '10.40.0.11', 'type': 'InternalIP'}, {'address': 'k8s01', 'type': 'Hostname'}]
        host = {}
        for addr in address_types:
            if addr.get('type', '') == 'InternalIP':
                host['ip'] = addr.get('address')
            elif addr.get('type', '') == 'Hostname':
                host['name'] = addr.get('address')
        hostnames[host['ip']] = host['name']
    return hostnames


def get_nfs_pods(namespace='hub'):
    """
    get pods
    {'dataset-dummy-1-rbd': {'host': 'k8s03'}}
    """
    hostnames = get_hostname()
    result = Run('kubectl get pod -n {} -o json'.format(namespace)).json()
    m = {}

    for pod in result['items']:
        if pod['metadata']['name'].startswith('nfs-'):
            hostIP = pod['status']['hostIP']
            for volume in pod['spec']['volumes']:
                if volume['name'] == 'mypvc':
                    name = volume['persistentVolumeClaim']['claimName']
                    m[name] = dict(host=hostnames[hostIP],
                                   hostIP=hostIP, uid=pod['metadata']['uid'], pod_name=pod['metadata']['name'])
    return m


def get_group_volume_list(namespace='hub'):
    result = Run('kubectl get pvc -n {} -o json'.format(namespace)).json()
    m = {}

    for pvc in result['items']:
        if pvc['status']['phase'] == 'Bound':
            name = pvc['metadata']['name']
            volumeName = pvc['spec']['volumeName']
            if name.endswith("-rbd"):
                m[name] = dict(volumeName=volumeName)
    return m


def get_user_volume_list(pvc_name=None, namespace='hub'):
    if pvc_name:
        result = [Run(
            'kubectl get pvc -n {namespace} {pvc_name} -o json'.format(namespace=namespace, pvc_name=pvc_name)).json()]
    else:
        result = Run(
            'kubectl get pvc -n {namespace} -o json'.format(namespace=namespace)).json()['items']
    m = {}

    for pvc in result:
        if pvc and pvc['status']['phase'] == 'Bound':
            name = pvc['metadata']['name']
            volumeName = pvc['spec']['volumeName']
            if name.startswith("claim-"):
                m[name] = dict(volumeName=volumeName)

    return m


def to_bytes(value, unit):
    unit_value = dict(M=1024**2, G=1024**3, T=1024**4)
    return int(value) * unit_value[unit]


def get_rbd_image_size(volumes, namespace='hub'):
    # for pvc in volume_list:
    for volume, attributes in volumes.items():
        stdout = Run('{} info replicapool/{}'.format(kubectl_rbd_cmd(),
                                                     attributes['volumeName'])).output()
        # we only care about the first char of [TGM]iB
        usage_result = re.findall(r'size (\d+) ([TGM])i?B', stdout)
        if usage_result:
            size, unit = usage_result[0]
            volumes[volume]['usage'] = dict(
                data=usage_result[0], size=to_bytes(size, unit))
    return volumes


def get_group_volume_usages():
    pods = get_nfs_pods()
    volumes = get_group_volume_list()
    merged = {}
    for k in pods.keys():
        merged[k] = {**pods[k], **volumes[k]}

    # TODO we don't need to get rbd image size so early
    get_rbd_image_size(merged)
    return merged


def get_user_volume_usages(pvc_name=None):
    volumes = get_user_volume_list(pvc_name)

    get_rbd_image_size(volumes)
    return volumes


if __name__ == "__main__":
    # TODO refactoring duplicated Popen
    print(get_ceph_image())
