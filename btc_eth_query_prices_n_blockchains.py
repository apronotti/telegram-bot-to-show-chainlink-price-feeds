"""
Basic example for a bot that uses inline keyboards. For an in-depth explanation, check out
 https://git.io/JOmFw.
"""
import logging
import requests
import time
import prettytable as pt
import datetime as dt

from web3 import Web3
from configuration.utils import Configuration

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram import ParseMode


class CLPriceFeedsTelegramBot:

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    
    # basic cache implementation
    cache = {"ETHUSD": None, "BTCUSD": None}
    cachetime = {"ETHUSD": time.time(), "BTCUSD": time.time()}
    
    CACHE_DURATION = 60 * 5      # 5 minutes
    
    # ABI Interface to access to Chainlink price feeds
    ABI_CL_PRICE_FEED = '[{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"getRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'

    # Read configuration from config.json
    config = Configuration.load_json('config.json')
    web3_ethereum = Web3(Web3.HTTPProvider(config.ethereum.apiprovider))
    web3_polygon = Web3(Web3.HTTPProvider(config.polygon.apiprovider))
    web3_bsc = Web3(Web3.HTTPProvider(config.bsc.apiprovider))


    def hours_from_timestamp(self, timestampValue) -> str:
        # convert timestamp to string of datetime format
        date = str(dt.datetime.fromtimestamp(timestampValue))
        # extract hours without seconds
        hours = date[-8:][:-3]
        return hours

    # Query the price of ETH/USD from Ethereum, Polygon and Bsc networks
    def get_eth(self) -> str:
        addr = self.config.ethereum.cl_contract_address.etherusd
        contract = self.web3_ethereum.eth.contract(address=addr, abi=self.ABI_CL_PRICE_FEED)
        # ETH/USD price query from Ethereum mainnet
        latest_data = contract.functions.latestRoundData().call()
        ethereum_data = (
            'Ethereum', latest_data[1], self.hours_from_timestamp(latest_data[2]))

        addr = self.config.polygon.cl_contract_address.etherusd
        contract = self.web3_polygon.eth.contract(address=addr, abi=self.ABI_CL_PRICE_FEED)
        # ETH/USD price query from Polygon mainnet
        latest_data = contract.functions.latestRoundData().call()
        polygon_data = ('Polygon', latest_data[1], self.hours_from_timestamp(latest_data[2]))

        addr = self.config.bsc.cl_contract_address.etherusd
        contract = self.web3_bsc.eth.contract(address=addr, abi=self.ABI_CL_PRICE_FEED)
        # ETH/USD price query from Binance Smart Chain mainnet
        latest_data = contract.functions.latestRoundData().call()
        bsc_data = ('Bsc', latest_data[1], self.hours_from_timestamp(latest_data[2]))

        title = 'ETH/USD'
        return [title, ethereum_data, polygon_data, bsc_data]

    # Query the price of BTC/USD from Ethereum, Polygon and Bsc networks
    def get_btc(self) -> str:
        addr = self.config.ethereum.cl_contract_address.btcusd
        contract = self.web3_ethereum.eth.contract(address=addr, abi=self.ABI_CL_PRICE_FEED)
        # BTC/USD price query from Ethereum mainnet
        latest_data = contract.functions.latestRoundData().call()
        ethereum_data = (
            'Ethereum', latest_data[1], self.hours_from_timestamp(latest_data[2]))
    
        addr = self.config.polygon.cl_contract_address.btcusd
        contract = self.web3_polygon.eth.contract(address=addr, abi=self.ABI_CL_PRICE_FEED)
        # BTC/USD price query from Polygon mainnet
        latest_data = contract.functions.latestRoundData().call()
        polygon_data = ('Polygon', latest_data[1], self.hours_from_timestamp(latest_data[2]))
    
        addr = self.config.bsc.cl_contract_address.btcusd
        contract = self.web3_bsc.eth.contract(address=addr, abi=self.ABI_CL_PRICE_FEED)
        # BTC/USD price query from Binance Smart Chain mainnet
        latest_data = contract.functions.latestRoundData().call()
        bsc_data = ('Bsc', latest_data[1], self.hours_from_timestamp(latest_data[2]))
    
        title = 'BTC/USD'
        return [title, ethereum_data, polygon_data, bsc_data]
    
    
    def get_price(self, selected_option: str) -> str:
        if selected_option == "ETHUSD":
            return self.build_table(self.get_eth())
        elif selected_option == "BTCUSD":
            return self.build_table(self.get_btc())
        else:
            return self.build_table(self.get_eth())
    
    
    def start(self, update: Update, context: CallbackContext) -> None:
        self.menu_command()
    
    
    def button(self, update: Update, context: CallbackContext) -> None:
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query
    
        # CallbackQueries need to be answered, even if no notification to the user is needed
        # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
        query.answer()
    
        selected_option = query.data
    
        if (time.time() - self.cachetime[selected_option]) > self.CACHE_DURATION or self.cache[selected_option] == None:
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
    
    
    def build_table(self, data):
    
        table = pt.PrettyTable()
    
        table.field_names = ['Net', data[0], 'Update']
        table.align['Net'] = 'l'
        table.align[data[0]] = 'r'
        table.align['Update'] = 'r'
    
        for net, price, updated in data[1:]:
            # price 8 decimal places precision rounded and converted to integer number
            priceToShow = int(round(price / 10 ** 8, 0))
            table.add_row([net, priceToShow, updated])
    
        return table
    
    
    def main(self) -> None:
        """Run the bot."""
        # Create the Updater and pass it your bot's token.
        updater = Updater(self.config.telegram.token)
    
        updater.dispatcher.add_handler(CommandHandler('start', self.start))
        updater.dispatcher.add_handler(CallbackQueryHandler(self.button))
        updater.dispatcher.add_handler(CommandHandler('pricefeeds', self.menu_command))
    
        # Start the Bot
        updater.start_polling()
    
        # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT
        updater.idle()


botInstance = CLPriceFeedsTelegramBot()
botInstance.main()
