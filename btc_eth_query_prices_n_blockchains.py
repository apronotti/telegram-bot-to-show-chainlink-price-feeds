"""
example of how to develop a Telegram bot that consumes Chainlink price feeds
for BTC/USD and ETH/USD pair of assets from Ethereum, Polygon and
Binance Smart Chain mainnets.
"""
import logging
import time
import datetime as dt
import prettytable as pt

from web3 import Web3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import ParseMode
from configuration.utils import Configuration


def build_table(data):
    """ build a printable table from data """
    table = pt.PrettyTable()

    table.field_names = ['Net', data[0], 'Update']
    table.align['Net'] = 'l'
    table.align[data[0]] = 'r'
    table.align['Update'] = 'r'

    for net, price, updated in data[1:]:
        # price 8 decimal places precision rounded and converted to integer
        # number
        price_to_show = int(round(price / 10 ** 8, 0))
        table.add_row([net, price_to_show, updated])

    return table


def hours_from_timestamp(timestamp_value) -> str:
    """ convert timestamp to string of datetime format """
    date = str(dt.datetime.fromtimestamp(timestamp_value))
    # extract hours without seconds
    hours = date[-8:][:-3]
    return hours


class CLPriceFeedsTelegramBot:
    """ Chainlink Price Feeds Telegram bot """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO)
    logger = logging.getLogger(__name__)

    # basic cache implementation
    cache = {"ETHUSD": None, "BTCUSD": None}
    cachetime = {"ETHUSD": time.time(), "BTCUSD": time.time()}

    CACHE_DURATION = 60 * 5      # 5 minutes

    # Read configuration from config.json
    config = Configuration.load_json('config.json')

    # ABI Interface to access to Chainlink price feeds
    ABI_CL_PRICE_FEED = config.abi_cl_price_feed

    web3_ethereum = Web3(Web3.HTTPProvider(config.ethereum.apiprovider))
    web3_polygon = Web3(Web3.HTTPProvider(config.polygon.apiprovider))
    web3_bsc = Web3(Web3.HTTPProvider(config.bsc.apiprovider))

    def get_from_blockchain(self, contract_address, title) -> str:
        """ Query the price of ETH/USD or BTC/USD from Ethereum, Polygon and Bsc networks """
        contract = self.web3_ethereum.eth.contract(
            address=contract_address['ethereum'], abi=self.ABI_CL_PRICE_FEED)
        # price query from Ethereum mainnet
        latest_data = contract.functions.latestRoundData().call()
        ethereum_data = (
            'Ethereum',
            latest_data[1],
            hours_from_timestamp(
                latest_data[2]))

        contract = self.web3_polygon.eth.contract(
            address=contract_address['polygon'], abi=self.ABI_CL_PRICE_FEED)
        # price query from Polygon mainnet
        latest_data = contract.functions.latestRoundData().call()
        polygon_data = (
            'Polygon',
            latest_data[1],
            hours_from_timestamp(
                latest_data[2]))

        contract = self.web3_bsc.eth.contract(
            address=contract_address['bsc'], abi=self.ABI_CL_PRICE_FEED)
        # price query from Binance Smart Chain mainnet
        latest_data = contract.functions.latestRoundData().call()
        bsc_data = (
            'Bsc',
            latest_data[1],
            hours_from_timestamp(
                latest_data[2]))

        return [title, ethereum_data, polygon_data, bsc_data]

    def get_price(self, selected_option: str) -> str:
        """ get the prices selected in the menu """
        contract_address = ""
        title = ""
        if selected_option == "ETHUSD":
            contract_address = dict(ethereum=self.config.ethereum.cl_contract_address.etherusd,
                                    polygon=self.config.polygon.cl_contract_address.etherusd,
                                    bsc=self.config.bsc.cl_contract_address.etherusd)
            title = "ETH/USD"
        elif selected_option == "BTCUSD":
            contract_address = dict(ethereum=self.config.ethereum.cl_contract_address.btcusd,
                                    polygon=self.config.polygon.cl_contract_address.btcusd,
                                    bsc=self.config.bsc.cl_contract_address.btcusd)
            title = "BTC/USD"

        data = self.get_from_blockchain(contract_address, title)

        return build_table(data)

    def start(self, update: Update, context: CallbackContext) -> None:
        """ start the bot """
        self.menu_command()

    def button(self, update: Update, context: CallbackContext) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query

        # CallbackQueries need to be answered, even if no notification
        # to the user is needed
        # Some clients may have trouble otherwise. See
        # https://core.telegram.org/bots/api#callbackquery
        query.answer()

        selected_option = query.data

        time_from_last_query = time.time() - self.cachetime[selected_option]

        if time_from_last_query > self.CACHE_DURATION or self.cache[selected_option] is None:
            table = self.get_price(selected_option)
            self.cache[selected_option] = table
            self.cachetime[selected_option] = time.time()
            print("no cache")
        else:
            table = self.cache[selected_option]
            print("cache")

        query.edit_message_text(
            text=f'<pre>{table}</pre>', parse_mode=ParseMode.HTML)

    def menu_command(self, update: Update, context: CallbackContext) -> None:
        """Sends a message with three inline buttons attached."""
        keyboard = [
            [InlineKeyboardButton("ETH/USD price", callback_data='ETHUSD')],
            [InlineKeyboardButton("BTC/USD price", callback_data='BTCUSD')],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        update.message.reply_text(
            'Please choose an option:', reply_markup=reply_markup)

    def main(self) -> None:
        """Run the bot."""
        # Create the Updater and pass it your bot's token.
        updater = Updater(self.config.telegram.token)

        updater.dispatcher.add_handler(CommandHandler('start', self.start))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))
        updater.dispatcher.add_handler(CommandHandler('pricefeeds',
                                       self.menu_command))

        # Start the Bot
        updater.start_polling()

        # Run the bot until the user presses Ctrl-C or
        # the process receives SIGINT,
        # SIGTERM or SIGABRT
        updater.idle()

if __name__ == '__main__':
    bot_instance = CLPriceFeedsTelegramBot()
    bot_instance.main()
