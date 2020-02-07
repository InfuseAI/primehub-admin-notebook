def is_orphan_dataset(datasets, pvc):
    if not datasets:
        return False
    for d in datasets:
        if 'dataset-' + d == pvc:
            return False
    return True

def is_orphan_group(groups, pvc):
    if not groups:
        return False
    for d in groups:
        if 'project-' + d.get('name') == pvc:
            return False
    return True

def is_orphan_user(users, pvc):
    if not users:
        return False
    for d in users:
        if 'claim-' + d == pvc:
            return False
    return True
