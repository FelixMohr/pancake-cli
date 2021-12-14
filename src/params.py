import os
from web3 import Web3


class Params(object):

    def __init__(self, web3: Web3):
        self.pair_contract = web3.eth.contract()
        self.target_token_contract = web3.eth.contract()
        self.pk = os.getenv("PRIVATE_KEY")
        self.wallet = web3.eth.account.privateKeyToAccount(self.pk)
        self.token0 = ""
        self.token1 = ""
        self.amount = 1.0
        self.base_token = ""
        self.target_token_number = 0
        self.slippage_percent = 1.0
        self.gas_price = 5
        self.use_busd = True
        self.decimals = 18
        self.target_token = ""
        self.target_symbol = ""
