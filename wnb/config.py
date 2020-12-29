import logging
from dataclasses import dataclass, field
from functools import reduce
from os.path import dirname, exists, realpath, sep
from sys import argv
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger()


def getConfigurationFilePath(path: Optional[str]) -> str:
    if path is not None and path != '':
        return path

    return f'{dirname(realpath(argv[0]))}{sep}.wnb.yml'


regionsList = ['us', 'eu', 'kr', 'tw', 'cn']
localizationList = {
    'English (United States)': 'en_US',
    'Spanish (Mexico)': 'es_MX',
    'Portuguese ': 'pt_BR',
    'German ': 'de_DE',
    'English (Great Britain)': 'en_GB',
    'Spanish (Spain)': 'es_ES',
    'French ': 'fr_FR',
    'Italian ': 'it_IT',
    'Russian ': 'ru_RU',
    'Korean ': 'ko_KR',
    'Chinese (Traditional)': 'zh_TW',
    'Chinese (Simplified)': 'zh_CN',
}


@dataclass
class Configuration:
    clientId: str = field(default='')
    clientSecret: str = field(default='')

    localization: str = field(default='')
    region: str = field(default='')
    realm: str = field(default='')
    character: str = field(default='')
    statWeights: Dict[str, float] = field(default_factory=lambda: {})

    def loadFile(self, data: dict) -> 'Configuration':
        if 'client' in data:
            client = data['client']
            if 'id' in client:
                self.clientId = client['id']
            if 'secret' in client:
                self.clientSecret = client['secret']

        for attr in [
                'localization', 'region', 'realm', 'character', 'statWeights'
        ]:
            if attr in data:
                self.__setattr__(attr, data[attr])

        return self

    def __setattr__(self, attr: str, value: Any):
        if attr == 'statWeights':
            super().__setattr__(attr, {})
            if isinstance(value, str):
                vals = value.split(',')
                if len(vals) == 1 and vals[0] == '':
                    value = {}
                else:
                    value = reduce(lambda a, x: a + [tuple(x.split('='))],
                                   vals, [])
                    value = dict(value)
                    for key in value.keys():
                        value[key] = float(value[key])

        super().__setattr__(attr, value)

    def validate(self) -> bool:
        if self.region not in ['', *regionsList]:
            logger.error(
                'Invalid region ({region}), expected one of: [{list}]'.format(
                    region=self.region, list=', '.join(regionsList)))
            return False

        localeValues = localizationList.values()
        if self.localization not in ['', *localeValues]:
            logger.error(
                'Invalid locale ({locale}), expected one of: [{list}]'.format(
                    locale=self.localization, list=', '.join(localeValues)))
            return False

        return True

    def write(self, path: Optional[str] = None) -> bool:
        if not self.validate():
            return False

        configFilePath = getConfigurationFilePath(path)
        with open(configFilePath, 'w') as f:
            yaml.dump(self.dump(), f)

        return True

    def dump(self) -> dict:
        return {
            'client': {
                'id': self.clientId,
                'secret': self.clientSecret,
            },
            'localization': self.localization,
            'region': self.region,
            'realm': self.realm,
            'character': self.character,
            'statWeights': self.statWeights,
        }


def readConfiguration(configFilePath: Optional[str] = None) -> Configuration:
    configFilePath = getConfigurationFilePath(configFilePath)

    conf = Configuration()

    logger.info(f'Loading configuration file: {configFilePath}')

    if not exists(configFilePath):
        logger.info('Configuration file does not exist, creating default one')
        conf.write(configFilePath)
        return conf

    with open(configFilePath) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

        return conf.loadFile(data)

    logger.warning('Unhandled code branch')

    return conf
