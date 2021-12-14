import json
import os
from halo import Halo
from web3 import Web3
from src.helpers import info, set_decimals
from src.params import Params

with open('abis/pair.json') as f:
    pair_abi = json.loads(f.read())
with open('abis/router.json') as f:
    router_abi = json.loads(f.read())
with open('abis/erc20.json') as f:
    erc20_abi = json.loads(f.read())
WBNB = '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c'
BUSD = "0xe9e7cea3dedca5984780bafc599bd69add087d56"
ws_url = os.getenv('WS_URL')
provider = Web3.WebsocketProvider(ws_url)
web3 = Web3(provider)
router_contract_addr = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
router_contract = web3.eth.contract(address=web3.toChecksumAddress(router_contract_addr), abi=router_abi)
busd_contract = web3.eth.contract(address=web3.toChecksumAddress(BUSD), abi=erc20_abi)


def create_params():
    return Params(web3)


def get_busd_contract():
    return busd_contract


def set_pair_and_print_info(address: str, params: Params):
    set_pair(address, params)
    info("done setting pair contract to " + str(params.pair_contract.address))
    info("traded tokens are " + str(params.token0) + " " + str(params.token1))
    info("(base token is token " + str(
        1 - params.target_token_number) +
         ")")
    info("target token is " + str(params.target_token_contract.address) + " (" + params.target_symbol + ")")
    info("decimals are " + str(params.decimals))


@Halo(text='Retrieving allowance', spinner='dots', text_color='magenta')
def get_allowance(token, wallet):
    router_address = router_contract.address
    allowance = token.functions.allowance(web3.toChecksumAddress(wallet.address),
                                          web3.toChecksumAddress(router_address)).call()
    return allowance


@Halo(text='Setting pair', spinner='dots', text_color='magenta')
def set_pair(address: str, params: Params):
    params.pair_contract = web3.eth.contract(address=web3.toChecksumAddress(address), abi=pair_abi)
    params.token0 = params.pair_contract.functions.token0().call()
    params.token1 = params.pair_contract.functions.token1().call()
    if params.token0 == WBNB:
        params.target_token_number = 1
        params.target_token = params.token1
        params.base_token = params.token0
    elif params.token0 == BUSD:
        params.target_token_number = 1
        params.target_token = params.token1
        params.base_token = params.token0
    elif params.token1 == WBNB:
        params.target_token_number = 0
        params.target_token = params.token0
        params.base_token = params.token1
    else:
        # token1 == BUSD
        params.target_token_number = 0
        params.target_token = params.token0
        params.base_token = params.token1
    params.target_token_contract = web3.eth.contract(address=web3.toChecksumAddress(params.target_token), abi=erc20_abi)
    params.decimals = params.target_token_contract.functions.decimals().call()
    params.target_symbol = params.target_token_contract.functions.symbol().call()


@Halo(text='Retrieving amounts', spinner='dots', text_color='magenta')
def get_amounts_out(params: Params):
    if params.base_token == WBNB:
        amount_out = router_contract.functions.getAmountsOut(set_decimals(params.amount, params.decimals),
                                                      [web3.toChecksumAddress(BUSD),
                                                       web3.toChecksumAddress(WBNB),
                                                       web3.toChecksumAddress(params.target_token)]).call()
        base_result = amount_out[2]
        result = Web3.fromWei(base_result, 'ether')
    else:
        amount_out = router_contract.functions.getAmountsOut(set_decimals(params.amount, params.decimals),
                                                      [web3.toChecksumAddress(BUSD),
                                                       web3.toChecksumAddress(params.target_token)]).call()
        base_result = amount_out[1]
        result = Web3.fromWei(base_result, 'ether')

    base_min_amount = round(base_result * (1 - params.slippage_percent / 100.0))
    min_amount = Web3.fromWei(base_min_amount, 'ether')
    return result, base_result, min_amount, base_min_amount


def balance(token_contract, wallet, decimals):
    spinner = Halo(text='Fetching balances', spinner='dots', text_color='magenta')
    spinner.start()
    busd_contract = web3.eth.contract(address=web3.toChecksumAddress(BUSD), abi=erc20_abi)
    wallet_address = wallet.address
    target_balance = token_contract.functions.balanceOf(wallet_address).call()
    busd_balance = busd_contract.functions.balanceOf(wallet_address).call()
    target_symbol = token_contract.functions.symbol().call()
    spinner.info("BUSD: {}, {}: {}".format(int(busd_balance) / 18.0, target_symbol, float(target_balance) / decimals))


def approve(token, wallet):
    spinner = Halo(text='Approving token spend', spinner='dots', text_color='magenta')
    spinner.start()
    max_amount = web3.toWei(2 ** 64 - 1, 'ether')
    allowance = get_allowance(token, router_contract, wallet)
    if allowance == max_amount:
        spinner.info("\nspending is already approved. skipping.")
        spinner.stop()
        return
    wallet_address = wallet.address
    nonce = web3.eth.getTransactionCount(wallet_address)
    pk = os.getenv("PRIVATE_KEY")
    tx = token.functions.approve(web3.toChecksumAddress(router_contract.address), max_amount).buildTransaction({
        'from': wallet_address,
        'nonce': nonce
    })

    signed_tx = web3.eth.account.signTransaction(tx, pk)
    try:
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        hex_hash = web3.toHex(tx_hash)
        spinner.info("https://etherscan.io/tx/{}".format(hex_hash))
    except ValueError as e:
        spinner.warn("could not send transaction, error:" + str(e))
    finally:
        spinner.stop()
