
# Kubernetes Management Tasks

This is a demo notebook for common kubernetes tasks.

*Note: You should be aware of where and how the jupyter session is running, as kubernetes credentials are sensitive information and leakage posts security risks.*

## Configure kubectl

If you did not start this notebook with pre-configured KUBECONFIG, you may paste your `kubectl config view --raw --minify` output here.  Otherwise skip to the next section.

Notes:
1. if you use gke, your `kubectl config` contains a token that a valid for an hour. Run `kubectl get cs` to refresh token locally before copying the config.


```python
import ipywidgets
from kubeconfig import KubeConfig
k = KubeConfig()
k.test()
```


```python
k.setup()
```

## Check version and cluster health


```python
!! kubectl version
```


```python
!! kubectl get cs
```


```python
!! kubectl get node
```

## Delete user pvc
Run the cell to render a dropdown list, select user pvc for deletion.


```python
user_pvcs = !! kubectl get -l component=singleuser-storage  pvc -n hub -o jsonpath='{range.items[*]}{.metadata.name}{"\n"}{end}'

pvc = ipywidgets.Dropdown(
    options=user_pvcs,
    description='Target:',
    disabled=False,
)
pvc
```

Run the cell to execute the deletion.


```python
def execute():
    if pvc.value is None:
        print("No selected PVC")
        return

    mounted_by = !! ~/bin/kubectl -n hub describe pvc {pvc.value} | grep -o 'jupyter-.*'

    if mounted_by:
        print("PVC %s can't be deleted because it's mounted by: %s" % (pvc.value, mounted_by[0]))
    else:
        result = !! ~/bin/kubectl -n hub delete pvc {pvc.value}
        print(result)

execute()
```

## Create pv-type dataset
Run the cell to render a dropdown list, select Target where to create a dataset.


```python
pv_type_datasets = !! kubectl -n hub get datasets -o=custom-columns=VOLUME_NAME:spec.volumeName,NAME:metadata.name,TYPE:spec.type | grep -e 'pv$' | grep -v -e '^hostpath:' | awk '{print $1","$2}'
temp_datasets = {}
for ds in pv_type_datasets:
    [volume_name, name] = ds.split(',')
    temp_datasets[name] = volume_name
dataset_name = ipywidgets.Dropdown(
    options=temp_datasets.keys(),
    description='Target:',
    disabled=False,
)
dataset_name
```

Run the cell to render a input field of `dataset size`, specify a size for the dataset which we want to create.


```python
dataset_size = ipywidgets.IntText(description='Size:', value=200)
dataset_size
```

Run the cell to determine the `storage_class`.


```python
is_rook_block = !! kubectl get sc | grep rook-block

storage_class = 'rook-block' if is_rook_block else 'standard'
storage_class
```

Run the cell to generate a yaml string of configuration.


```python
dataset_volume = temp_datasets[dataset_name.value]

pv_type_dataset_yaml_string = '''apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  annotations:
    primehub-group: dataset-%s
    primehub-group-sc: %s
  name: dataset-%s
  namespace: hub
spec:
  accessModes:
  - ReadWriteMany
  dataSource: null
  resources:
    requests:
      storage: %s
  selector:
    matchLabels:
      primehub-group: dataset-%s
      primehub-namespace: hub
  storageClassName: ''
''' % (dataset_volume, storage_class, dataset_volume, str(dataset_size.value)+'Gi', dataset_volume)
print(pv_type_dataset_yaml_string)
```

Run the cell to apply generated yaml for dataset creation.


```python
!! echo "{pv_type_dataset_yaml_string}" | kubectl -n hub apply -f -
```
