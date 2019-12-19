import requests

def get_primehub_info(url, secret):
    payload = {'query': '{groups{name enabledSharedVolume} datasets{name type volumeName} users{username}}'}
    headers = {'Authorization': 'Bearer %s'%secret}
    response = requests.post(url, payload, headers=headers)
    primehub_info = response.json().get('data',{})
    return primehub_info
