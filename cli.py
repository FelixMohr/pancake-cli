import concurrent

import os

from src.core import set_pair_and_print_info, get_allowance, get_amounts_out, balance, approve, create_params, \
    get_busd_contract, swap
from src.helpers import info, set_decimals


def main():
    with open("files/cake.txt") as f:
        content = f.read()
        print(content)

    params = create_params()
    pair_contract = os.getenv('PAIR_CONTRACT')
    if pair_contract:
        set_pair_and_print_info(pair_contract, params)

    while True:
        inp = input(' 🐰    >>> ').strip()
        split = inp.split()
        if not len(split):
            continue
        command = split[0]
        args = split[1:]
        try:
            if command == 'pair':
                set_pair_and_print_info(args[0], params)
            elif command == 'price':
                show_price(params)
            elif command == 'amount':
                params.amount = float(args[0])
                info("amount set to " + str(params.amount))
            elif command == 'slippage':
                params.slippage_percent = float(args[0])
                info("slippage set to " + str(params.slippage_percent) + "%")
            elif command == 'sell-percentage':
                params.sell_percentage = int(args[0])
                blnc = balance(params.target_token_contract, params.wallet, params.decimals)
                params.sell_amount = blnc
                info("sell percentage set to " + str(params.sell_percentage) + "%")
            elif command == 'sell-amount':
                params.sell_amount = set_decimals(float(args[0]), params.decimals)
                info("sell amount set to " + str(params.sell_amount / 10 ** 18))
            elif command == 'sprice':
                show_price(params, True)
            elif command == 'allowance':
                if len(args) and args[0].lower().strip() == "busd":
                    info("allowance is " + str(get_allowance(get_busd_contract(), params.wallet)))
                else:
                    info("allowance is " + str(
                        get_allowance(params.target_token_contract, params.wallet)))
            elif command == 'approve':
                if len(args) and args[0].lower().strip() == "busd":
                    approve(get_busd_contract(), params.wallet)
                else:
                    approve(params.target_token_contract, params.wallet)
            elif command == 'balance':
                balance(params.target_token_contract, params.wallet, params.decimals)
            elif command == 'gas':
                params.gas_price = int(args[0])
                info("new gas price for swaps is {}".format(params.gas_price))
            elif command == 'quit':
                break
            elif command == 'buy':
                swap(params)
            elif command == 'sell':
                swap(params, True)
            else:
                info('Invalid Command.')
        except concurrent.futures._base.TimeoutError:
            info("Timeout error – provider or BSC may be down")
            info("Please try again")
        except ValueError as e:
            info("Value error:")
            info(str(e))


def show_price(params, sale=False):
    amount_out, _, min_out, _ = get_amounts_out(params, sale)
    if not sale:
        price_per_1 = round(params.amount / float(amount_out), 10)
    else:
        price_per_1 = round(float(amount_out) / params.amount, 10)
    info("amount out per " + str(params.amount) + " is " + str(amount_out) +
         " (price per 1 {} = ".format(params.target_symbol) + str(
        price_per_1) + ")")
    info("minimum received with slippage " + str(params.slippage_percent) + "% -> " + str(min_out))


if __name__ == "__main__":
    main()
