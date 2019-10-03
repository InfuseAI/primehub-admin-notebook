import requests

url = 'https://hub.kent.dev.primehub.io/graphql'
payload = {'query': '{groups{name enabledSharedVolume} datasets{name type volumeName} users{username}}'}
secret = '1228101f93b387e08a1bb99a53b363f2036678d565d3321cf522a2af8ca84c93'
headers = {'Authorization': 'Bearer %s'%secret}

def get_primehub_info(url, secret):
    payload = {'query': '{groups{name enabledSharedVolume} datasets{name type volumeName} users{username}}'}
    headers = {'Authorization': 'Bearer %s'%secret}
    response = requests.post(url, payload, headers=headers)
    primehub_info = response.json().get('data',{})
    return primehub_info