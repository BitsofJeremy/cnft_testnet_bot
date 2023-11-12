# config.py

import os

# Set a bot version
BOT_VERSION = '0.0.7'

# Database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'tokens_testnet.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
SQLALCHEMY_TRACK_MODIFICATIONS = True

# IPFS
BLOCKFROST_IPFS = os.getenv('BLOCKFROST_IPFS')

# Token
TESTNET_ID = os.getenv('TESTNET_ID')
CARDANO_CLI = "/Applications/Daedalus\ Testnet.app/Contents/MacOS/cardano-cli"
BLOCKFROST_TESTNET = os.getenv('BLOCKFROST_TESTNET')

# Other
# Set the cushion to about an hour
SLOT_CUSHION = 3600
