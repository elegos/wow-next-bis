import logging
from datetime import datetime

import pandas as pd

import confSetup
from wnb import config, itemCache

logger = logging.getLogger()

conf = config.readConfiguration()
client = confSetup.setup(conf=conf)

# Open the items cache
itemCache.getItemCache().loadCache()

logger.info("Reading character's equipment...")
equipment = client.getCharacterEquipment()
subclassIds = []
for equip in equipment.items():
    subclassIds.append(equip[1]['item_subclass']['id'])
subclassIds = list(set(subclassIds))

logger.info('Reading top items...')
topItems = []
for slot in equipment:
    topItems.extend(
        client.getTopItems(minLevel=equipment[slot]['level'], slot=slot))


def wowheadLink(itemId: int) -> str:
    baseUrl = 'https://{lang}.wowhead.com/item={itemId}'
    lang = {
        'en_US': 'www',
        'es_MX': 'es',
        'pt_BR': 'pt',
        'de_DE': 'de',
        'en_GB': 'www',
        'es_ES': 'es',
        'fr_FR': 'fr',
        'it_IT': 'it',
        'ru_RU': 'ru',
        'ko_KR': 'ko',
        'zh_TW': 'cn',
        'zh_CN': 'cn',
    }[conf.localization]

    return baseUrl.format(lang=lang, itemId=itemId)


def rank(itemData):
    rank = 0
    for stat in conf.statWeights.items():
        itemStatsRaw = itemData['preview_item'][
            'stats'] if 'stats' in itemData['preview_item'] else None
        if itemStatsRaw is None:
            continue

        itemStat = next(
            iter([s for s in itemStatsRaw if s['type']['type'] == stat[0]]),
            {'value': 0})
        rank += itemStat['value'] * stat[1]

    return rank


logger.info('Ranking items based on given stat weights...')
for item in equipment.items():
    item[1]['rank'] = rank(item[1])

flatItems = []
for item in topItems:
    equipType = item['inventory_type']['type']
    equippedItem = equipment[equipType] if equipType in equipment else None
    equipped = 'X' if equippedItem is not None and item['id'] == equippedItem[
        'id'] else ''

    if item['item_subclass']['id'] not in subclassIds:
        continue

    flatItems.append({
        'id': item['id'],
        'name': item['name'],
        'level': item['level'],
        'slot': item['inventory_type']['type'],
        'rank': rank(item),
        'equipped': equipped,
        'wowhead_url': wowheadLink(item["id"]),
    })

logger.info('Sorting by rank...')
dataframe = pd.DataFrame(flatItems)
dataframe.sort_values(by=['slot', 'rank'],
                      ascending=[True, False],
                      inplace=True)

logger.info('Currently equipped ranking:')
for slot in equipment.keys():
    rank = equipment[slot]['rank']
    logger.info(f'- {slot}: {rank}')

    dataframe = dataframe.loc[(dataframe['slot'] == slot) &
                              (dataframe['rank'] >= rank) |
                              (dataframe['slot'] != slot)]

outputName = f'{conf.character}_{datetime.now().strftime("%Y%m%d")}.xlsx'
logger.info(f'Generating {outputName}...')
dataframe.to_excel(outputName, index=False)

# Write the items cache
itemCache.getItemCache().writeCache()
