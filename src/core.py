import json
import os
from halo import Halo
from web3 import Web3
from src.helpers import info, set_decimals
from src.params import Params
import time

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
    return Params(web3, os.getenv("PRIVATE_KEY"))


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
def get_amounts_out(params: Params, sale=False):
    token_to = params.target_token
    token_from = BUSD
    amount = params.amount
    decimals = 18
    if sale:
        token_to = BUSD
        token_from = params.target_token
        amount = params.sell_amount
        decimals = params.decimals

    try:
        if params.base_token == WBNB:
            amount_out = router_contract.functions.getAmountsOut(set_decimals(amount, decimals),
                                                                 [web3.toChecksumAddress(token_from),
                                                                  web3.toChecksumAddress(WBNB),
                                                                  web3.toChecksumAddress(token_to)]).call()
            base_result = amount_out[2]
            result = Web3.fromWei(base_result, 'ether')
        else:
            amount_out = router_contract.functions.getAmountsOut(set_decimals(amount, decimals),
                                                                 [web3.toChecksumAddress(token_from),
                                                                  web3.toChecksumAddress(token_to)]).call()
            base_result = amount_out[1]
            result = Web3.fromWei(base_result, 'ether')
    except ValueError:
        base_result = 0
        result = 0

    base_min_amount = round(base_result * (1 - params.slippage_percent / 100.0))
    min_amount = Web3.fromWei(base_min_amount, 'ether')
    return result, base_result, min_amount, base_min_amount


def balance(token_contract, wallet, decimals):
    spinner = Halo(text='Fetching balances', spinner='dots', text_color='magenta')
    spinner.start()
    wallet_address = wallet.address
    target_balance = token_contract.functions.balanceOf(wallet_address).call()
    busd_balance = busd_contract.functions.balanceOf(wallet_address).call()
    target_symbol = token_contract.functions.symbol().call()
    spinner.info("BUSD: {}, {}: {}".format(int(busd_balance) / 18.0, target_symbol, float(target_balance) / decimals))
    return busd_balance, target_balance


def approve(token, wallet):
    spinner = Halo(text='Approving token spend', spinner='dots', text_color='magenta')
    spinner.start()
    max_amount = web3.toWei(2 ** 64 - 1, 'ether')
    allowance = get_allowance(token, wallet)
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
        spinner.info("https://bscscan.io/tx/{}".format(hex_hash))
    except ValueError as e:
        spinner.warn("could not send transaction, error:" + str(e))
    finally:
        spinner.stop()


def swap(params: Params, sale=False):
    if sale:
        spinner = Halo(text='Selling token', spinner='dots', text_color='magenta')
    else:
        spinner = Halo(text='Buying token', spinner='dots', text_color='magenta')
    spinner.start()
    wallet_address = params.wallet.address
    nonce = web3.eth.getTransactionCount(wallet_address)
    pk = os.getenv("PRIVATE_KEY")

    if params.base_token == WBNB:
        path = [web3.toChecksumAddress(BUSD), web3.toChecksumAddress(WBNB), web3.toChecksumAddress(params.target_token)]
    else:
        path = [web3.toChecksumAddress(BUSD), web3.toChecksumAddress(params.target_token)]
    if sale:
        path.reverse()

    amount = params.sell_amount
    if not sale:
        amount = set_decimals(params.amount, 18)

    print(amount)
    _, _, _, min_returned = get_amounts_out(params, sale)
    # expire in 90s
    deadline = int(round(time.time() * 1000)) + 90 * 1000

    try:
        tx = router_contract.functions.swapExactTokensForTokensSupportingFeeOnTransferTokens(amount, min_returned, path,
                                                                                             web3.toChecksumAddress(
                                                                                                 params.wallet.address),
                                                                                             deadline) \
            .buildTransaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': 10000000,
            'gasPrice': web3.toWei(params.gas_price, 'gwei')
        })
        signed_tx = web3.eth.account.signTransaction(tx, pk)
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        hex_hash = web3.toHex(tx_hash)
        spinner.info("https://bscscan.io/tx/{}".format(hex_hash))
    except ValueError as e:
        spinner.warn("could not send transaction, error:" + str(e))
    finally:
        spinner.stop()
