
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

## Delete User Volume

Run the cell to render a dropdown list, select user pvc for deletion.

```python
import ipywidgets
import time

user_pvcs = ! kubectl get -l component=singleuser-storage  pvc -n hub -o jsonpath='{range.items[*]}{.metadata.name}{"\n"}{end}'
user_list = [user[len('claim-'):] for user in user_pvcs]

def multi_checkbox_widget(descriptions):
    """ Widget with a search field and lots of checkboxes """
    search_widget = ipywidgets.Text()
    options_dict = {description: ipywidgets.Checkbox(description=description, value=False, layout=ipywidgets.Layout(height='20px')) for description in descriptions}
    options = [options_dict[description] for description in descriptions]
    options_widget = ipywidgets.VBox(options, layout={'overflow': 'scroll'})
    multi_select = ipywidgets.VBox([search_widget, options_widget])

    # Wire the search field to the checkboxes
    def on_text_change(change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = [options_dict[description] for description in descriptions]
        else:
            matches = [x for x in descriptions if x.startswith(search_input)]
            new_options = [options_dict[description] for description in matches]
        options_widget.children = new_options

    search_widget.observe(on_text_change, names='value')
    return multi_select

def execute(self):
    selected_options = [w.description for w in multi_checkbox.children[1].children if w.value]
    print('Start to delete %s pvc...' % len(selected_options))

    for user in selected_options:
        pvc = 'claim-' + user
        mounted_by = ! ~/bin/kubectl -n hub describe pvc {pvc} | grep 'Mounted By:' | grep -v '<none>'

        if mounted_by:
            print("PVC %s can't be deleted because it's mounted by: %s" % (pvc, mounted_by[0]))
        else:
            ! ~/bin/kubectl -n hub delete pvc {pvc}
    print('Completed')

def select_all_onclick(self):
    def check(x):
        x.value = True
        time.sleep(0.03)
    [check(w) for w in multi_checkbox.children[1].children]

def inverse_select_onclick(self):
    def check(x):
        x.value = not x.value
        time.sleep(0.03)
    [check(w) for w in multi_checkbox.children[1].children]

select_all_btn = ipywidgets.Button(description="Select All", button_style="info", layout=ipywidgets.Layout(width='80px'), style=ipywidgets.ButtonStyle(button_color='#365abd'))
select_all_btn.on_click(select_all_onclick)
inverse_select_btn = ipywidgets.Button(description="Inverse", button_style="info", layout=ipywidgets.Layout(width='80px'), style=ipywidgets.ButtonStyle(button_color='#6490e8'))
inverse_select_btn.on_click(inverse_select_onclick)
delete_btn = ipywidgets.Button(description="Delete", button_style="danger", layout=ipywidgets.Layout(width='80px'), style=ipywidgets.ButtonStyle(button_color='#d13a1f'))
delete_btn.on_click(execute)
multi_checkbox = multi_checkbox_widget(user_list)

ipywidgets.HBox([
    multi_checkbox,
    select_all_btn,
    inverse_select_btn,
    delete_btn
])
```

## Delete Group Volume

Run the cell to render a dropdown list, select group volume pvc for deletion.

```python
import ipywidgets
import time

group_pvcs = !! kubectl get pvc -n hub | grep 'hub-nfs-.*' | grep -v '^dataset-.*' | cut -d' ' -f1

def multi_checkbox_widget(descriptions):
    """ Widget with a search field and lots of checkboxes """
    search_widget = ipywidgets.Text()
    options_dict = {description: ipywidgets.Checkbox(description=description, value=False, layout=ipywidgets.Layout(height='20px')) for description in descriptions}
    options = [options_dict[description] for description in descriptions]
    options_widget = ipywidgets.VBox(options, layout={'overflow': 'scroll'})
    multi_select = ipywidgets.VBox([search_widget, options_widget])

    # Wire the search field to the checkboxes
    def on_text_change(change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = [options_dict[description] for description in descriptions]
        else:
            matches = [x for x in descriptions if x.startswith(search_input)]
            new_options = [options_dict[description] for description in matches]
        options_widget.children = new_options

    search_widget.observe(on_text_change, names='value')
    return multi_select

def execute(self):
    selected_options = [w.description for w in multi_checkbox.children[1].children if w.value]
    print('Start to delete %s pvc...' % len(selected_options))
    for pvc in selected_options:
        mounted_by = ! ~/bin/kubectl -n hub describe pvc {pvc} | grep 'Mounted By:' | grep -v '<none>'

        if mounted_by:
            print("PVC %s can't be deleted because it's mounted by: %s" % (pvc, mounted_by[0]))
        else:
            print("Start to delete pvc %s ..." % pvc)
            pvc_delete = ! ~/bin/kubectl -n hub delete pvc {pvc}
            print(pvc_delete)
            print("Start to delete sts pvc data-nfs-%s-0 ..." % pvc)
            sts_pvc_delete = ! ~/bin/kubectl -n hub delete pvc data-nfs-{pvc}-0
            print(sts_pvc_delete)
    print('Completed')

def select_all_onclick(self):
    def check(x):
        x.value = True
        time.sleep(0.03)
    [check(w) for w in multi_checkbox.children[1].children]

def inverse_select_onclick(self):
    def check(x):
        x.value = not x.value
        time.sleep(0.03)
    [check(w) for w in multi_checkbox.children[1].children]

select_all_btn = ipywidgets.Button(description="Select All", button_style="info", layout=ipywidgets.Layout(width='80px'), style=ipywidgets.ButtonStyle(button_color='#365abd'))
select_all_btn.on_click(select_all_onclick)
inverse_select_btn = ipywidgets.Button(description="Inverse", button_style="info", layout=ipywidgets.Layout(width='80px'), style=ipywidgets.ButtonStyle(button_color='#6490e8'))
inverse_select_btn.on_click(inverse_select_onclick)
delete_btn = ipywidgets.Button(description="Delete", button_style="danger", layout=ipywidgets.Layout(width='80px'), style=ipywidgets.ButtonStyle(button_color='#d13a1f'))
delete_btn.on_click(execute)
multi_checkbox = multi_checkbox_widget(group_pvcs)

ipywidgets.HBox([
    multi_checkbox,
    select_all_btn,
    inverse_select_btn,
    delete_btn
])
```

## Cleanup released orphan PV

Run the cell to render a list, select delete button to delete orphan PV.

**This run will delete your PV data and can't recover!!!**

```python
released_pvs = ! kubectl get pv | grep Retain | grep Released | awk '{print $1, $6}'

tbody = []

def orphan_pv_handler(self):
    pv = self.tooltip
    if pv is "" or self.description is "Deleted":
        return
    patch = '\'{"spec":{"persistentVolumeReclaimPolicy": "Delete"}}\''
    ! kubectl patch pv $pv -p $patch
    self.description="Deleted"
    self.button_style=''
    pass

for res in released_pvs:
    pv, pvc = res.split(' ', 1)
    pvc_lable = ipywidgets.Label(value="pvc: %s" % pvc)
    pv_lable = ipywidgets.Label(value="pv: %s" % pv)
    delete_button = ipywidgets.Button(description="Delete", button_style="danger", tooltip=pv)
    delete_button.on_click(orphan_pv_handler)
    tbody.append(ipywidgets.HBox([delete_button, pvc_lable, pv_lable]))

ipywidgets.VBox(tbody)

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

## Resize Group Volume

Run the cell to render a dropdown list, select group volume to resize

```python
import ipywidgets
from resizevolume.usage import *
from resizevolume.resize import *

group_volume = ipywidgets.Dropdown(
    options=get_group_volume_list().keys(),
    description='Group vol:',
    disabled=False,
)

group_volume
```

Run the cell to render a input field of group volume size, specify a size for the group volume which we want to resize.

```python
usage = get_group_volume_usages(group_volume.value)

num, unit = usage.get(group_volume.value).get('usage').get('data')

new_usage = ipywidgets.BoundedIntText(
    value=num,
    min=num,
    max=9999,
    step=1,
    description='New Size:',
    disabled=False)

def resize_handler(self):
    resize_group_volume(group_volume.value, str(new_usage.value) + unit)

resize_btn = ipywidgets.Button(description="Update", button_style="danger")
resize_btn.on_click(resize_handler)

ipywidgets.HBox([
    ipywidgets.Label(value="Current Size: %s %s" % (num, unit)),
    new_usage,
    ipywidgets.Label(value=unit),
    resize_btn])
```

## Resize User Volume

Run the cell to render a dropdown list, select user volume to resize

```python
import ipywidgets
from resizevolume.usage import *
from resizevolume.resize import *

user_volume = ipywidgets.Dropdown(
    options=get_user_volume_list().keys(),
    description='User vol:',
    disabled=False,
)
""
user_volume

```

Run the cell to render a input field of user volume size, specify a size for the user volume which we want to resize.

```python
usage = get_user_volume_usages(user_volume.value)

num, unit = usage.get(user_volume.value).get('usage').get('data')

new_usage = ipywidgets.BoundedIntText(
    value=num,
    min=num,
    max=9999,
    step=1,
    description='New Size:',
    disabled=False)

def resize_handler(self):
    resize_user_volume(user_volume.value, str(new_usage.value) + unit)

resize_btn = ipywidgets.Button(description="Update", button_style="danger")
resize_btn.on_click(resize_handler)

ipywidgets.HBox([
    ipywidgets.Label(value="Current Size: %s %s" % (num, unit)), new_usage,
    ipywidgets.Label(value=unit),
    resize_btn])
```
