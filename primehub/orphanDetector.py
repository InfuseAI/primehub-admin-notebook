def is_orphan_dataset(datasets, pvc):
    for d in datasets:
        if 'dataset-' + d.get('volumeName') == pvc and d.get('type') == 'pv':
            return False
    return True

def is_orphan_group(groups, pvc):
    for d in groups:
        if 'project-' + d.get('name') == pvc:
            return False
    return True

def is_orphan_user(users, pvc):
    for d in users:
        if 'claim-' + d.get('username') == pvc:
            return False
    return True
