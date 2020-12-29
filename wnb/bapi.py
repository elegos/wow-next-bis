from datetime import datetime
from functools import reduce
from typing import Dict, List, Optional
from time import sleep

import requests as req

from wnb.config import Configuration
from wnb.itemCache import getItemCache

AUTH_API_URL = 'https://{region}.battle.net'
API_URL = 'https://{region}.api.blizzard.com'

token: Optional[str] = None
tokenExpiration = datetime.now()


class BAPI:
    conf: Configuration
    token: str
    tokenExpiration: datetime

    def __init__(self, conf: Configuration):
        self.conf = conf
        self.token = ''
        self.tokenExpiration = datetime.now()

    def authenticate(self,
                     grantType: str = 'client_credentials',
                     scope: List[str] = ['wow.profile']):
        if self.token != '' and self.tokenExpiration > datetime.now():
            return

        url = AUTH_API_URL.format(region=self.conf.region) + '/oauth/token'
        response = req.post(url,
                            auth=(self.conf.clientId, self.conf.clientSecret),
                            data={'grant_type': grantType})

        if response.status_code != 200:
            raise Exception(
                f'Invalid authentication, status code: {response.status_code}')

        data = response.json()

        self.token = data['access_token']
        self.tokenExpiration = datetime.fromtimestamp(
            datetime.now().timestamp() + data['expires_in'])

    def get(self,
            uri: str,
            namespace: str = '',
            queryParams: dict = {}) -> Optional[req.Response]:
        try:
            self.authenticate()
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/json'
            }
            if namespace != '':
                headers.update({'Battlenet-Namespace': namespace})

            response = req.get(API_URL.format(region=self.conf.region) + uri,
                               params=queryParams,
                               headers=headers)

            if response.status_code >= 400:
                raise Exception(
                    'Invalid API status code for {uri}: {code}'.format(
                        uri=uri, code=response.status_code))

            return response
        except Exception as e:
            print(e)

            return None

    def post(self,
             uri: str,
             queryParams: dict = {},
             payload: dict = {}) -> req.Response:
        self.authenticate()

    def realmsList(self) -> Dict[str, str]:
        connectedRealms = self.get('/data/wow/search/connected-realm',
                                   namespace=f'dynamic-{self.conf.region}',
                                   queryParams={
                                       'locale': self.conf.localization,
                                       '_page': 1
                                   })
        if connectedRealms is None:
            return
        connectedRealms = connectedRealms.json()['results']

        def reduceMain(accumulated: List[tuple], item: dict) -> List[str]:
            for realm in item['data']['realms']:
                accumulated.append({
                    'name':
                    realm['name'][self.conf.localization],
                    'slug':
                    realm['slug']
                })

            return accumulated

        return sorted(reduce(reduceMain, connectedRealms, []),
                      key=lambda obj: obj['name'])

    def getCharacterEquipment(self) -> dict:
        response = self.get(
            uri='/profile/wow/character/{realm}/{name}/equipment'.format(
                realm=self.conf.realm, name=self.conf.character.lower()),
            namespace=f'profile-{self.conf.region}',
            queryParams={'locale': self.conf.localization})

        if response is None:
            return

        data = response.json()
        result = {}
        for item in data['equipped_items']:
            itemData = self.getItemData(item['item']['id'])
            result[item['slot']['type']] = itemData

        return result

    def getItemData(self, itemId: int) -> dict:
        cache = getItemCache()
        cached = cache.getItem(itemId)
        if cached is not None:
            return cached

        response = self.get(
            uri=f'/data/wow/item/{itemId}',
            namespace=f'static-{self.conf.region}',
            queryParams={'locale': self.conf.localization},
        )
        if response is None:
            return

        itemData = response.json()
        cache.setItem(itemId, itemData)

        return itemData

    def getTopItems(self, minLevel: int, slot: str) -> dict:
        page = 1
        results = []
        while page is not None:
            response = self.get(uri='/data/wow/search/item',
                                namespace=f'static-{self.conf.region}',
                                queryParams={
                                    'locale': self.conf.localization,
                                    'orderby': 'level:desc',
                                    '_page': page,
                                    '_pageSize': 1000,
                                    'level': f'({minLevel},{minLevel + 50}]',
                                    'inventory_type.type': slot,
                                })
            if response is None:
                return
            data = response.json()

            results.extend(data['results'])

            page = page + 1
            if page > data['pageCount']:
                page = None

        # Cool down API threshold
        sleep(1)

        final = []
        for item in results:
            item = self.getItemData(itemId=item['data']['id'])
            final.append(item)

        return [
            item for item in final
            if item['inventory_type']['type'] != 'NON_EQUIP'
        ]
