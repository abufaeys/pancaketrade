"""Utilities for web3 interaction."""
from json.decoder import JSONDecodeError
from pathlib import Path

import requests
from loguru import logger
from pancaketrade.persistence import Abi, db
from web3.types import ChecksumAddress


def fetch_abi(contract: ChecksumAddress, api_key: str) -> str:
    out = ''
    try:
        with db:
            abi = Abi.get(Abi.address == contract)
        out = abi.abi
    except Abi.DoesNotExist:
        r = requests.get(
            'https://api.bscscan.com/api',
            params={
                'module': 'contract',
                'action': 'getabi',
                'address': contract,
                'apikey': api_key,
            },
        )
        try:
            res = r.json()
        except JSONDecodeError:
            logger.warning('ABI decode error, falling back to default ABI.')
            with Path('pancaketrade/utils/bep20.abi').open('r') as f:
                return f.read()
        out = res['result']
        if out[0] != '[':  # abi starts with a square bracket, otherwise we got a message from bscscan
            logger.warning('ABI not found, falling back to default ABI.')
            with Path('pancaketrade/utils/bep20.abi').open('r') as f:
                return f.read()
        try:
            db.connect()
            with db.atomic():
                Abi.create(address=contract, abi=res['result'])
        except Exception as e:
            logger.error(f'Failed to create database record: {e}')
            return ''
    return out
