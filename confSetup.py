import getopt
import logging
import sys
from functools import reduce
from typing import List

import inquirer

from wnb import bapi, config

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger()


def confPrompts(checks: List[tuple], conf: config.Configuration) -> None:
    questions = []

    for check in checks:
        if conf.__getattribute__(check[0]) != '':
            continue

        if len(check) == 2:
            questions.append(inquirer.Text(check[0], message=check[1]))
        if len(check) == 3:
            questions.append(
                inquirer.List(check[0], message=check[1], choices=check[2]))

    answers = inquirer.prompt(questions)
    for item in answers.items():
        conf.__setattr__(item[0], item[1])


def setup(conf: config.Configuration) -> bapi.BAPI:
    opts = ('hdi:s:l:c:w:', [
        'client-id=', 'client-secret=', 'region=', 'realm=', 'locale=',
        'character=', 'debug', 'help', 'weights='
    ])
    optlist, args = getopt.getopt(sys.argv[1:], *opts)

    optionsCoords = {
        '-i': 'clientId',
        '--client-id': 'clientId',
        '-s': 'clientSecret',
        '--client-secret': 'clientSecret',
        '-l': 'localization',
        '--locale': 'localization',
        '--region': 'region',
        '--realm': 'realm',
        '-c': 'character',
        '--character': 'character',
        '-w': 'statWeights',
        '--weights': 'statWeights',
    }

    logger.setLevel(logging.INFO)
    for opt in optlist:
        if opt[0] in ['-d', '--debug']:
            logger.setLevel(logging.DEBUG)

        if opt[0] in ['-h', '--help']:
            # yapf: disable
            print('WoW Next BiS')
            print('')
            print('Options: (-v value, --variable="value"')
            print(' -i, --client-id: set the API client id (required the first time) (if empty, choice is prompted)')  # noqa: E501
            print(' -s, --client-secret: set the API client secret (required the first time) (if empty, choice is prompted)')  # noqa: E501
            print(' -l, --locale: set the preferred locale (if empty, choice is prompted)')  # noqa: E501
            print('     --region: set the region (if empty, choice is prompted)')  # noqa: E501
            print('     --realm: set the realm (if empty, choice is prompted)')  # noqa: E501
            print(' -c, --character: set the character (if empty, choice is prompted)')  # noqa: E501
            print(' -w, --weights: "STAT1=weight1,STAT2=weight2" comma separated (if empty, choice is prompted)')  # noqa: E501
            print('                AGILITY, INTELLECT, STAMINA, STRENGTH,')  # noqa: E501
            print('                CRIT_RATING, HASTE_RATING, MASTERY_RATING')  # noqa: E501
            print('                example: -w "INTELLECT=1,CRIT_RATING=0.2,HASTE_RATING=0.7"')  # noqa: E501
            # yapf: enable
            sys.exit()

        if opt[0] in optionsCoords:
            conf.__setattr__(optionsCoords[opt[0]], opt[1])

    client = bapi.BAPI(conf)
    # yapf: disable
    checks = [
        ('clientId', 'API client id'),
        ('clientSecret', 'API client secret'),
        ('localization', 'Locale', list(config.localizationList.values())),
        ('region', 'Region', config.regionsList),
    ]
    # yapf: enable
    confPrompts(checks, conf)

    logger.info('Reading realms list...')
    realms = client.realmsList()

    # yapf: disable
    checks = [
        ('realm', 'Realm', reduce(lambda a, x: a + [x['name']], realms, [])),
        ('character', 'Character name'),
    ]
    confPrompts(checks, conf)

    if len(conf.statWeights) == 0:
        answers = inquirer.prompt([
            inquirer.Checkbox('stats',
                              message='Stats to weight',
                              choices=[
                                  'AGILITY',
                                  'INTELLECT',
                                  'STAMINA',
                                  'STRENGTH',
                                  'CRIT_RATING',
                                  'HASTE_RATING',
                                  'MASTERY_RATING',
                                  'VERSATILITY',
                              ])
        ])
        questions = [
            inquirer.Text(stat,
                          message=f'Weight ({stat})',
                          validate=lambda _, value: float(value) > 0)
            for stat in answers['stats']
        ]

        answers = inquirer.prompt(questions)
        weights = {}
        for answer in answers.items():
            weights[answer[0]] = float(answer[1])
        conf.statWeights = weights

    realmBySlug = next(
        iter([realm for realm in realms if realm['slug'] == conf.realm]), None)
    realmByName = next(
        iter([realm for realm in realms if realm['name'] == conf.realm]), None)

    if realmByName is None and realmBySlug is None:
        print(f'Could not find realm ({conf.realm})')
    if realmByName is not None:
        conf.realm = realmByName['slug']

    if not conf.write():
        print('Could not write configuration file')
        sys.exit()

    return client
