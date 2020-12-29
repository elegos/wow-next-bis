# WoW Next BiS

Python script to help you choose your next item to hunt down.

WORK IN PROGRESS - any suggestion is welcome.

## Prerequisites

- Python 3
- pipenv (`pip install pipenv`)
- API credentials ([here](https://develop.battle.net/access/)) - only the application's name is required.
- Updated stat weights (for example from [here](https://www.raidbots.com/simbot/stats))

## How to use
- `pipenv install` (once)
- `pipenv run python main.py`

It will generate an excel file to read and profit from.

In order to change the settings, either edit `.wnb.yml` or run the script with the relative options (see `pipenv run python main.py --help`). In order to be prompted for one or more settings, just set it blank (i.e. `--weights=""`)

## How it works
The ONLY mechanic implemented here (the poor's man drop optimizer) is the stats weight. It ranks the items multiplying the stat values by their weights, then it sorts them up and serves to you.
