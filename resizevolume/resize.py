#!/usr/bin/env python3
import re
import os
from subprocess import Popen, PIPE
import json
from .command import Run
from .usage import *
import sys
import time
namespace = 'hub'

def get_cwd():
    print(os.getcwd())

def resize_rbd_image(group, new_size):
    print('[Resize RBD Image]')
    log = Run('{rbd_cmd} resize -p replicapool --size {size} {pv}'.format(
        rbd_cmd=kubectl_rbd_cmd(), size=new_size, pv=group['volumeName']))
    print(log.communicate()[1])


def get_block_device(pod_name, namespace='hub'):
    result = Run("kubectl exec -n {namespace} {pod_name} -- mount".format(namespace=namespace, pod_name=pod_name)
                 ).pipe('grep rbd')
    mount_info = result.output()
    if mount_info:
        reObj = re.findall(r'(.+) on .+ type (.+) ', mount_info)[0]
        tool = dict(xfs='xfs_growfs', ext4='resize2fs')
        return {'block_device': reObj[0], 'resize_tool': tool[reObj[1]], 'image': get_ceph_image()}
    return {}


def resize_rbd_filesystem(group):
    print('[Resize RBD FileSystem]')
    cmd = get_block_device(group['pod_name'])

    with open("resizevolume/resize_filesystem.yaml", "r") as fh:
        job_spec = fh.read().format(**{**group, **cmd})
        import io
        Run("kubectl delete job -n primehub resize-volume-filesystem")
        stdout, stderr = Popen(
            "kubectl apply -f -".split(' '), stdin=PIPE, stdout=PIPE).communicate(input=job_spec.encode('utf8'))

    while True:
        job_status = Run(
            'kubectl get job -n primehub resize-volume-filesystem -o json').json()
        if job_status:
            if job_status['status'].get('succeeded', None):
                break
        time.sleep(1)

    print(Run('kubectl logs -n primehub -l app=resize-script').output())
    Run("kubectl delete job -n primehub -l app=resize-script")
    Run("kubectl delete pod -n hub -l app=resize-script")


def check_new_size(group, new_size):
    reObj = re.findall(r'(\d+)([GMT])', new_size)
    if reObj:
        size, unit = reObj[0]
        bytes = to_bytes(size, unit)
        current_size = group['usage']['size']
        return (bytes > current_size)
    else:
        print('Error: incorrect size: {}\n'.format(new_size))
        return False


def resize_gke_pvc(pvc_name, new_size):
    cmd = 'kubectl patch -n hub pvc %s --type merge --patch {"spec":{"resources":{"requests":{"storage":"%si"}}}}' % (pvc_name, new_size)
    out, err = Run(cmd).communicate()
    if err:
        print('Error: %s' % err)
        return False
    print(out)
    return True

# Step: Resize Group Volume
#   1. Check input
#   2. Check nfs pv
#   3. Get pv name
#   5. Resize rbd image
#   6. Resize rbd file system


def resize_group_volume(pvc_name, new_size):
    usage_volumes = get_group_volume_usages(pvc_name)
    group = usage_volumes.get(pvc_name, None)
    if not group:
        print('Error: not such Group Volume: {}\n'.format(pvc_name))
        return False

    if not check_new_size(group, str(new_size)):
        print('Error: size can only be increased:'.format(new_size))
        size, unit = group['usage']['data']
        print('       Current : {}{}'.format(size, unit))
        print('       New     : {}'.format(new_size))
        return False

    pv = get_pv_by_volume_name(group['volumeName'])
    storageClass = pv['spec']['storageClassName']

    if storageClass == 'rook-block':
        resize_rbd_image(group, new_size)
        resize_rbd_filesystem(group)
    else:
        resize_gke_pvc(pvc_name, new_size)

# Step: Resize User Volume
# check_input
# get pv name
# get pod name
# resize_rbd_image
# resize2fs_block
# kubectl get pod -o wide -n hub -o json | jq '.items[] | select(.metadata.name == "jupyter-test") | .spec.nodeName' <== have node info
# kubectl get pod -o wide -n hub -o json | jq '[.items[] | select(.metadata.name == "jupyter-test") | {"host":.spec.nodeName, "name":.metadata.name}]'


def resize_user_volume(pvc_name, new_size):
    usage_volumes = get_user_volume_usages(pvc_name)
    user = usage_volumes.get(pvc_name, None)

    if not user:
        print('Error: not such User Volume: {}\n'.format(pvc_name))
        return False

    if not check_new_size(user, str(new_size)):
        print('Error: size can only be increased:'.format(new_size))
        size, unit = user['usage']['data']
        print('       Current : {}{}'.format(size, unit))
        print('       New     : {}'.format(new_size))
        return False

    pv = get_pv_by_volume_name(user['volumeName'])
    storageClass = pv['spec']['storageClassName']

    if storageClass == 'rook-block':
        pod = get_user_volume_pod(pvc_name)
        if not pod:
            print('No pod found')
            return False

        user = {**user, **pod}

        resize_rbd_image(user, new_size)

        resize_rbd_filesystem(user)

        return True
    else:
        return resize_gke_pvc(pvc_name, new_size)

def _get_pod_info(pvc_name, namespace='hub', wait_for_running_count=5):
    m = {}
    result = Run('kubectl describe pvc -n {namespace} {pvc_name}'.format(
        namespace=namespace, pvc_name=pvc_name)).pipe('grep Mounted')
    pod_name = result.output().strip().split()[-1]
    if pod_name == '<none>':
        return None

    pod = Run('kubectl get pod -o wide -n {namespace} {pod_name} -o json'.format(
        namespace=namespace, pod_name=pod_name)).json()
    if not pod:
        return None

    if pod['status']['phase'] == 'Running':
        m['host'] = pod['spec']['nodeName']
        m['pod_name'] = pod_name
        return m

    while wait_for_running_count > 0:
        wait_for_running_count = wait_for_running_count - 1
        time.sleep(5)
        return _get_pod_info(pod_name, namespace, wait_for_running_count)
    print("Cannot get pod info")
    return None


def get_user_volume_pod(pvc_name, namespace='hub'):
    print('[Check user volume pod]')
    pod_name = pvc_name.replace('claim', 'jupyter')

    m = _get_pod_info(pvc_name)
    if m:
        return m

    # Create temporarily pod
    print('[Create temporarily Pod for resizing]')
    resize_pod = 'resizevolume/resize-user-volume-' + pod_name
    with open("resizevolume/resize_user_volume_pod_spec.yaml", "r") as fh:
        pod_spec = fh.read().format(image=get_ceph_image(),
                                    resize_pod=resize_pod, pvc_name=pvc_name)
        import io
        Run("kubectl delete job -n primehub resize-volume-filesystem")
        stdout, stderr = Popen(
            "kubectl apply -f -".split(' '), stdin=PIPE, stdout=PIPE).communicate(input=pod_spec.encode('utf8'))
        time.sleep(1)
        # wait for pod started
        m = _get_pod_info(pvc_name)
    return m


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('Usage: {} [group | user] <pvc name> <new size>'.format(
            sys.argv[0]))
        sys.exit(1)

    func = {}
    func['group'] = resize_group_volume
    func['user'] = resize_user_volume

    operator = func.get(sys.argv[1], None)
    if not operator:
        print('Usage: {} [group | user] <pvc name> <new size>'.format(
            sys.argv[0]))
        sys.exit(1)
    operator(*sys.argv[2:])
