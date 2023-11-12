# Telegram Bot for issuing NFTs on the Cardano TESTNET using Python

This bot uses the `python-telegram-bot` framework to build out a nice little bot to create NFTs on the Cardano TESTNET blockchain.

Read more here:  [BLOG_LINK](https://blog.deafmice.com/building-a-nft-minting-bot-with-cardano-telegram-and-python-introduction/)

### Pre-install

This bot uses [blockfrost.io](https://blockfrost.io) for two functions, one for uploading and pinning IPFS data, and the other to get transaction details.

You will also need a bot setup in Telegram via the @botfather

This app assumes you are on a Mac and uses the default Daedalus installed for cli operations


### Install

Clone the repo, change into it, and make a tmp directory

    git clone https://gitlab.com/deafmice/cnft_testnet_bot.git
    cd cnft_testnet_bot
    mkdir tmp

Setup a virtualenv

    virtualenv -p python3 venv
    source venv/bin/activate

pip install requirements

    pip install -r requirements.txt

source the .env file [see example below]

    source .env

Change any of the settings in `config.py` for your setup [Optional] 

    nano config.py

create the database

    python db_model.py

run the bot

    python app.py

Some notes:

 - All logs are stored in `logging.log`
 - Token metadata and transactions are stored in the DB
 - There will be temporary files in the `tmp/` directory. A cleanup script will need to be written. 


### Example .env file

Replace with your secrets.

    # Blockfrost API
    export BLOCKFROST_IPFS=YOUR_SECRET_KEY
    export BLOCKFROST_TESTNET=YOUR_SECRET_KEY
    
    # Telegram Bot API Key
    export BOT_API_TOKEN=YOUR_SECRET_KEY
    
    # Cardano Node on Testnet in Daedalus TESTNET install MacOS
    export CARDANO_NODE_SOCKET_PATH=~/Library/Application\ Support/Daedalus\ Testnet/cardano-node.socket
    export TESTNET_ID=1097911063
