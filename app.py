# app.py

import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, \
    Filters, CallbackContext, ConversationHandler, Defaults
from uuid import uuid4
import logging

# Local Imports
import config
from db_model import Session, Tokens
from ipfs_utils import create_ipfs, pin_ipfs
from token_utils import pre_mint, mint, get_tx_details, check_wallet_utxo

logging.basicConfig(
    level=logging.INFO,
    filename='logging.log',
    filemode='w',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.info('****** cNFT TESTNET BOT START ******')

API_TOKEN = os.getenv('BOT_API_TOKEN')
# Conversation STATES
PHOTO, TICKER, NAME, DESCRIPTION, NUMBER, PRE_MINT = range(6)


def get_chat_info(chat_update):
    """ Helper function to gather some chat details """
    msg_dict = {
        'username': chat_update.message.from_user.username,
        'user_id': chat_update.message.from_user.id,
        'message_id': chat_update.message.message_id,
        'is_bot': chat_update.message.from_user.is_bot
    }
    logging.info("******* CHAT INFO ********")
    logging.info(msg_dict)
    logging.info("***************")
    return msg_dict


def start(update: Update, context: CallbackContext) -> int:
    """ Starts the whole process """
    chat_info = get_chat_info(chat_update=update)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Welcome @{chat_info['username']} to the *cNFT TESTNET Bot*."
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="We will be preforming the following actions in this session: \n"
             " - Uploading and Pinning a photo to IPFS \n"
             " - Gathering the token metadata from you (Ticker, Name, etc.)\n"
             " - Funding the token creator account to create the token (5 ADA) \n"
             " - Minting the token and returning it back to the address sending the initial funds \n"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="_Note: The 5 ADA will be returned to the address "
             "sending the initial funds subtracting the required "
             "token minting fees (~2-3 ADA)._"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"bot version: v{config.BOT_VERSION} \n"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please begin by uploading a *PHOTO* using the PHOTO "
             "upload feature in your Telegram client to start the minting process."
             "\n I will then upload it to IPFS, pin it, and return the IPFS hash."
    )
    return PHOTO


def photo(update: Update, context: CallbackContext) -> int:
    chat_info = get_chat_info(chat_update=update)
    photo_file = update.message.photo[-1].get_file()
    logging.info(update.message.photo[-1])
    file_name = f"{chat_info['username']}_{chat_info['user_id']}_{chat_info['message_id']}.jpg"
    photo_file.download(file_name)
    # Upload to BF
    res = create_ipfs(image=file_name)
    if res:
        # Pin it
        pin_response = pin_ipfs(ipfs_hash=res['ipfs_hash'])
        if pin_response:
            update.message.reply_text(
                "Hooray! Your image has been uploaded to IPFS and pinned:"
            )
            update.message.reply_text(
                f"Here is a handy link for you to keep. \n"
                f"https://gateway.ipfs.io/ipfs/{res['ipfs_hash']}"
            )
            context.user_data["token_ipfs_hash"] = res['ipfs_hash']
        else:
            update.message.reply_text(
                'Something failed here? Pin to blockfrost.io failed.'
            )
            return ConversationHandler.END
    else:
        update.message.reply_text(
            'Something failed here? Upload to blockfrost.io failed.'
        )
        return ConversationHandler.END
    # Remove left overs
    os.remove(file_name)
    # Respond to get ticker
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="What will the 4-5 character token ticker be for your NFT? (examples: TEST0, DOGE1) \n"
             "Please enter that now."
    )
    return TICKER


def skip_photo(update: Update, _: CallbackContext) -> int:
    """ User has chosen to not upload an image, End the session. """
    user = update.message.from_user
    logging.info(f"User {user.username} did not send a photo.")
    update.message.reply_text(
        'Process Ended. Use /start to try again.'
    )
    return ConversationHandler.END


def put_ticker(update: Update, context: CallbackContext) -> int:
    """ PUT the TICKER to the users context """
    logging.info(f'RAW DATA ENTERED: {update.message.text}')
    token_ticker = update.message.text
    context.user_data["token_ticker"] = token_ticker.upper()
    update.message.reply_text(
        f'Great! Your TICKER will be: {update.message.text}')
    update.message.reply_text(
        'Thank you, what will the name of'
        ' your token be? (Example: TestToken0) \n'
        'Please enter that now.'
    )
    return NAME


def put_token_name(update: Update, context: CallbackContext) -> int:
    """ PUT the TOKEN NAME to the users context """
    logging.info(f'RAW DATA ENTERED: {update.message.text}')
    context.user_data["token_name"] = update.message.text
    update.message.reply_text(f'Awesome! Your TOKEN NAME will be: {update.message.text}')
    update.message.reply_text(
        'Thank you, what will the description of your token be? (example: Just a test) \n'
        'Please enter that now.'
    )
    return DESCRIPTION


def put_token_desc(update: Update, context: CallbackContext) -> int:
    """ PUT the TOKEN DESCRIPTION to the users context """
    logging.info(f'RAW DATA ENTERED: {update.message.text}')
    context.user_data["token_desc"] = update.message.text
    update.message.reply_text(f'Sweet! Your TOKEN DESCRIPTION will be: {update.message.text}')
    update.message.reply_text(
        'Thank you, if this is a series of tokens, \n'
        'what will the number of your token be? (example: 0, 1, 2, 3, etc) \n'
        'Please enter that now.'
    )
    return NUMBER


def put_token_number(update: Update, context: CallbackContext) -> int:
    """ PUT the TOKEN NUMBER to the users context """
    logging.info(f'RAW DATA ENTERED: {update.message.text}')
    token_number = update.message.text
    if type(token_number) is str:
        logging.info("token_number is a string, doh!")
        token_number = 0
    context.user_data["token_number"] = token_number
    update.message.reply_text(f'Rad! Your TOKEN NUMBER will be: {update.message.text}')
    update.message.reply_text('Now we will begin the pre-minting process. \n')
    update.message.reply_text('Type OK to begin.')
    return PRE_MINT


def put_pre_mint(update: Update, context: CallbackContext) -> int:
    """ Starts pre-minting a token, returns an address to send funds to """
    auth = update.message.text
    if auth.lower() == 'ok':
        logging.info(f"We are a GO!")
        # Gather data
        logging.info(context.user_data)
        if context.user_data:
            session_uuid = str(uuid4())
            logging.info(session_uuid)
            context.user_data['session_uuid'] = session_uuid
            user = get_chat_info(update)
            nft_data = {
                'session_uuid': session_uuid,
                'creator_username': user['username'],
                'token_ticker': context.user_data.get('token_ticker', 'Not found'),
                'token_name': context.user_data.get('token_name', 'Not found'),
                'token_desc': context.user_data.get('token_desc', 'Not found'),
                'token_number': context.user_data.get('token_number', 'Not found'),
                'token_ipfs_hash': context.user_data.get('token_ipfs_hash', 'Not found'),
            }
            update.message.reply_text(
                "Here is the token metadata data we will be using to create a NFT. \n"
            )
            update.message.reply_text(
                f'*token_ticker*: {nft_data["token_ticker"]} \n'
                f'*token_name*: {nft_data["token_name"]} \n'
                f'*token_desc*: {nft_data["token_desc"]} \n'
                f'*token_number*: {nft_data["token_number"]} \n'
                f'*token_ipfs_hash*: {nft_data["token_ipfs_hash"]} \n'
            )
            update.message.reply_text("Setting up the NFT metadata...")
            pre_minted = pre_mint(**nft_data)
            if pre_minted:
                # Means we updated the DB and have a addr to send funds to
                # Start DB Session to get addr
                session = Session()
                sesh_exists = session.query(Tokens).filter(
                    Tokens.session_uuid == session_uuid).scalar() is not None
                if sesh_exists:
                    token_data = session.query(Tokens).filter(
                        Tokens.session_uuid == session_uuid).one()
                    logging.info(f'Session Data Created: {token_data}')
                    logging.info(f'Bot Address: {token_data.bot_payment_addr}')
                    # At this point we need the bot_payment_addr to have UTXO to burn
                    update.message.reply_text(f'Please deposit 5 ADA in the following address:')
                    update.message.reply_text(f'*{token_data.bot_payment_addr}*')
                    update.message.reply_text(
                        f'Once transaction has been confirmed in your wallet, \n'
                        f'run the /MINT command.')
                    return ConversationHandler.END
                else:
                    update.message.reply_text("No Session Data yet. /start to begin.")
                    return ConversationHandler.END
            else:
                update.message.reply_text("Pre-mint failed, check bot logs.")
                return ConversationHandler.END
        else:
            update.message.reply_text("No Data yet. /start to begin.")
            return ConversationHandler.END
    update.message.reply_text("No OK?!? /start to begin again.")
    return ConversationHandler.END


def put_mint(update: Update, context: CallbackContext) -> int:
    """ Returns the token data to user """
    session_uuid = context.user_data['session_uuid']
    user = get_chat_info(update)
    creator_username = user['username']

    # Start DB Session to get addr
    session = Session()
    sesh_exists = session.query(Tokens).filter(
        Tokens.session_uuid == session_uuid).scalar() is not None
    if sesh_exists:
        # Add a check for the UTXO, bail if not found
        token_data = session.query(Tokens).filter(
            Tokens.session_uuid == session_uuid).one()
        logging.info(f'Looking for UTXOs in bot address: {token_data}')
        bot_payment_addr = token_data.bot_payment_addr
        update.message.reply_text("Checking for transaction confirmation.")
        utxo = check_wallet_utxo(bot_payment_addr)
        if utxo:
            sesh = {'session_uuid': session_uuid}
            update.message.reply_text("OK, I found the Transaction, thank you.")
            update.message.reply_text(
                "Please be patient as I build your NFT "
                "and send it back to you with your change in ADA."
            )
            update.message.reply_text("Starting NFT Minting process......")
            minted = mint(**sesh)
            if minted:
                update.message.reply_text(
                    f"Awesome Sauce! \n I finished minting your token, @{creator_username}."
                )
                update.message.reply_text(
                    f"The token should arrive in your wallet shortly."
                )
                update.message.reply_text(
                    f"Thank you for using the *cNFT TESTNET Bot*. \n Have an ADA day."
                )
                return ConversationHandler.END
            else:
                update.message.reply_text(
                    f"Something failed, please try not to panic, "
                    f"but you may have hit a bug. Sorry."
                )
                return ConversationHandler.END
        else:
            update.message.reply_text(
                f"Sorry, but there is no UTXO to use yet. "
                f"Transaction not found."
                f"Please try running /MINT again in a few moments."
            )
            return ConversationHandler.END
    update.message.reply_text(
        f"Sorry, but there is no PRE_MINT session yet. "
        f"Please try /start again in a few moments."
    )
    return ConversationHandler.END

#
# Some Helper Chat Commands
#


def get_token_data(update: Update, context: CallbackContext) -> int:
    """ Returns the token data to user """
    if context.user_data:
        nft_data = {
            'token_ticker': context.user_data.get('token_ticker', 'Not found'),
            'token_name': context.user_data.get('token_name', 'Not found'),
            'token_desc': context.user_data.get('token_desc', 'Not found'),
            'token_number': context.user_data.get('token_number', 'Not found'),
            'token_ipfs_hash': context.user_data.get('token_ipfs_hash', 'Not found'),
        }
        update.message.reply_text(
            f'*token_ticker*: {nft_data["token_ticker"]} \n'
            f'*token_name*: {nft_data["token_name"]} \n'
            f'*token_desc*: {nft_data["token_desc"]} \n'
            f'*token_number*: {nft_data["token_number"]} \n'
            f'*token_ipfs_hash*: {nft_data["token_ipfs_hash"]} \n'
        )
    else:
        update.message.reply_text("No Data yet. Enter /start to begin.")
    return ConversationHandler.END


def get_tx(update: Update, context: CallbackContext) -> int:
    """ Returns the transaction data to user """
    # Need user to send tx hash
    tx_hash = context.args[0]
    logging.info(f"tx_hash: {tx_hash}")
    data = get_tx_details(tx_hash=tx_hash)
    logging.info(data)
    update.message.reply_text("Transaction found.")
    update.message.reply_text(
        f"{data}"
    )
    return ConversationHandler.END


def get_utxo(update: Update, context: CallbackContext) -> int:
    """ Returns the UTXO data to user """
    logging.info(context.args)
    update.message.reply_text("Enter an *address* to look up a transaction.")
    ada_addr = context.args[0]
    update.message.reply_text("Checking Transaction confirmation.")
    utxo = check_wallet_utxo(ada_addr)
    if utxo:
        update.message.reply_text("UTXO found.")
        update.message.reply_text(
            f"{utxo}"
        )
    else:
        update.message.reply_text("No transaction found.")
    return ConversationHandler.END


def cancel(update: Update, _: CallbackContext) -> int:
    """ User opted to end the conversation """
    user = update.message.from_user
    logging.info(f"User {user.username} canceled the conversation.")
    update.message.reply_text('Bye!')
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your token and private key
    updater = Updater(
        token=API_TOKEN,
        use_context=True,
        defaults=Defaults(parse_mode='Markdown')
    )

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Handlers
    # Add conversation handler with the states PHOTO, TICKER, NAME, DESCRIPTION, NUMBER, and PRE_MINT
    # TODO add skip functions for each state
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            PHOTO: [MessageHandler(Filters.photo, photo), CommandHandler('skip', skip_photo)],
            TICKER: [MessageHandler(Filters.text & ~Filters.command, put_ticker)],
            NAME: [MessageHandler(Filters.text & ~Filters.command, put_token_name)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, put_token_desc)],
            NUMBER: [MessageHandler(Filters.text & ~Filters.command, put_token_number)],
            PRE_MINT: [MessageHandler(Filters.text & ~Filters.command, put_pre_mint)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('get_token_data', get_token_data))
    dispatcher.add_handler(CommandHandler('get_tx', get_tx))
    dispatcher.add_handler(CommandHandler('get_utxo', get_utxo))
    dispatcher.add_handler(CommandHandler('MINT', put_mint))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()






