import os
import requests
from datetime import datetime, timezone

KEYCLOAK_ADMIN_USER = os.getenv('KEYCLOAK_ADMIN_USER', 'admin')
KEYCLOAK_ADMIN_PASSWORD = os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'password')
KEYCLOAK_HOST = os.getenv('KEYCLOAK_HOST', 'http://localhost:8080')
REALM = 'buildspace'
GROUPS_ENDPOINT = f'{KEYCLOAK_HOST}/auth/admin/realms/{REALM}/groups'

def main():
    token = get_token()
    groups = get_expired_groups(token)
    for group in groups:
        delete_group(token, group['id'])


def get_token():
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'client_secret': '',
        'username': KEYCLOAK_ADMIN_USER,
        'password': KEYCLOAK_ADMIN_PASSWORD
    }

    response = requests.post(f'{KEYCLOAK_HOST}/auth/realms/master/protocol/openid-connect/token', headers=headers, data=data)
    return response.json()['access_token']

def get_tmp_groups(token):
    response = requests.get(f'{GROUPS_ENDPOINT}/?search=tmp', headers={'Authorization': f'Bearer {token}'})
    tmpID = response.json()[0]['id']
    response = requests.get(f'{GROUPS_ENDPOINT}/{tmpID}', headers={'Authorization': f'Bearer {token}'})
    return response.json()['subGroups']

def get_expired_groups(token):
    groups = get_tmp_groups(token)
    now = datetime.now(timezone.utc)
    return [group for group in groups 
            if group['attributes']['expiration'][0] 
            and datetime.fromisoformat(group['attributes']['expiration'][0].replace('Z', '+00:00')) < now]

def delete_group(token, group_id):
    response = requests.delete(f'{GROUPS_ENDPOINT}/{group_id}', headers={'Authorization': f'Bearer {token}'})
    if response.status_code == 204:
        print(f'Deleted group with ID {group_id}')
    else:
        print(f'Failed to delete group with ID {group_id}. Status code: {response.status_code}')


if __name__ == '__main__':
    main()
