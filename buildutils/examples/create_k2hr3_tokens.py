#
# K2HDKC DBaaS based on Trove
#
# Copyright 2024 Yahoo Japan Corporation
#
# K2HDKC DBaaS is a Database as a Service compatible with Trove which
# is DBaaS for OpenStack.
# Using K2HR3 as backend and incorporating it into Trove to provide
# DBaaS functionality. K2HDKC, K2HR3, CHMPX and K2HASH are components
# provided as AntPickax.
# 
# For the full copyright and license information, please view
# the license file that was distributed with this source code.
#
# AUTHOR:   Hirotaka Wakabayashi
# CREATE:   Thu Oct 10 2024
# REVISION:
#

# Simple CUI application to get registerpath for k2hdkc dbaas.
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import argparse
import os
import sys
import json
import urllib.parse
import urllib.request

here = os.path.dirname(__file__)
src_dir = os.path.join(here, '..')
if os.path.exists(src_dir):
    sys.path.append(src_dir)

from k2hr3client.http import K2hr3Http
from k2hr3client.token import K2hr3Token
from k2hr3client.token import K2hr3RoleToken
from k2hr3client.token import K2hr3RoleTokenList

IDENTITY_V3_PASSWORD_AUTH_JSON_DATA = '''
{
    "auth": {
        "identity": {
            "methods": [
                "password"
            ],
            "password": {
                "user": {
                    "name": "admin",
                    "domain": {
                        "name": "Default"
                    },
                    "password": "devstacker"
                }
            } }
    }
}
'''

IDENTITY_V3_TOKEN_AUTH_JSON_DATA = '''
{
    "auth": {
        "identity": {
            "methods": [
                "token"
            ],
            "token": {
                "id": ""
            }
        },
        "scope": {
            "project": {
                "domain": {
                    "id": "default"
                },
                "name": ""
            }
        }
    }
}
'''

def get_scoped_token_id(url, user, password, project):
    # Get a scoped token id from openstack identity.
    # unscoped token-id
    # https://docs.openstack.org/api-ref/identity/v3/index.html#password-authentication-with-unscoped-authorization
    python_data = json.loads(IDENTITY_V3_PASSWORD_AUTH_JSON_DATA)
    python_data['auth']['identity']['password']['user']['name'] = user
    python_data['auth']['identity']['password']['user']['password'] = password  # noqa
    headers = {
        'User-Agent': 'hiwkby-sample',
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url,
                                 json.dumps(python_data).encode('ascii'),
                                 headers,
                                 method="POST")
    with urllib.request.urlopen(req) as res:
        unscoped_token_id = dict(res.info()).get('X-Subject-Token')
        # print('unscoped_token_id:[{}]'.format(unscoped_token_id))

    # scoped token-id
    # https://docs.openstack.org/api-ref/identity/v3/index.html?expanded=#token-authentication-with-scoped-authorization
    python_data = json.loads(IDENTITY_V3_TOKEN_AUTH_JSON_DATA)
    python_data['auth']['identity']['token']['id'] = unscoped_token_id
    python_data['auth']['scope']['project']['name'] = project
    headers = {
        'User-Agent': 'hiwkby-sample',
        'Content-Type': 'application/json'
    }
    req = urllib.request.Request(url,
                                 json.dumps(python_data).encode('ascii'),
                                 headers,
                                 method="POST")
    with urllib.request.urlopen(req) as res:
        scoped_token_id = dict(res.info()).get('X-Subject-Token')
        # print('scoped_token_id:[{}]'.format(scoped_token_id))
        return scoped_token_id


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='k2hr3 token api example')
    parser.add_argument(
        '--url',
        dest='url',
        default='http://127.0.0.1/identity/v3/auth/tokens',
        help='identity api url. ex) http://127.0.0.1/identity/v3/auth/tokens')  # noqa
    parser.add_argument('--user',
                        dest='user',
                        default='demo',
                        help='openstack user')
    parser.add_argument('--password',
                        dest='password',
                        default='password',
                        help='openstack user password')
    parser.add_argument('--project',
                        dest='project',
                        default='demo',
                        help='openstack project')
    parser.add_argument('--k2hr3_url',
                        dest='k2hr3_url',
                        default='http://localhost:18080',
                        help='k2hr3 api url')
    parser.add_argument('--role',
                        dest='role',
                        default='k2hdkccluster',
                        help='k2hr3 rolename')
    args = parser.parse_args()

    # 1. Gets a openstack token id from openstack identity server
    openstack_token = get_scoped_token_id(args.url, args.user, args.password,  # noqa
                                          args.project)

    # 2. Gets a k2hr3 token from the openstack token
    k2hr3_token = K2hr3Token(args.project, openstack_token)
    http = K2hr3Http(args.k2hr3_url)
    http.POST(k2hr3_token.create())

    # 3. Gets a k2hr3 role token from the k2hr3 token
    k2hr3_role_token = K2hr3RoleToken(k2hr3_token.token,
                                      role=args.role,
                                      expire=0)
    http.GET(k2hr3_role_token)
    roletoken = k2hr3_role_token.token
    print("roletoken {}".format(roletoken))

    # 4. Gets a k2hr3 role token list from the k2hr3 token
    k2hr3_role_token_list = K2hr3RoleTokenList(k2hr3_token.token,
                                               role=args.role,
                                               expand=True)
    http.GET(k2hr3_role_token_list)

    # 4. Gets the registerpath of the k2hr3 role token
    registerpath = k2hr3_role_token_list.registerpath(roletoken)
    print("{}".format(registerpath))
    sys.exit(0)

#
# Local variables:
# tab-width: 4
# c-basic-offset: 4
# End:
# vim600: noexpandtab sw=4 ts=4 fdm=marker
# vim<600: noexpandtab sw=4 ts=4
#
