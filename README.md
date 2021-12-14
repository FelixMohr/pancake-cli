# pancake-cli

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

This CLI can perform [Pancakeswap](https://pancakeswap.finance/) trades for you. 

## Installation
1. Create  virtual environment: `python -m venv venv`
2. `. venv/bin/activate`
3. `pip install -r requirements.txt`

## Using it

Set the environment variables:
* `PRIVATE_KEY` private key of your wallet to trade with
* `WS_URL` URL of web3 provider websocket (like [Quicknode](https://www.quicknode.com) or [Ankr](https://app.ankr.com/))
* `PAIR_CONTRACT` a Pancakeswap pair contract, e.g. 0x4Cb29498595A733c4B0d710E766BB89345eE945b

Then execute the following commands:

1. `. venv/bin/activate` (if not done yet)
2. `python cli.py` will start the CLI


### Commands
* _amount [AMOUNT]_: Set the amount to buy to AMOUNT BUSD
* _balance_: Shows your balance of the target token and of BUSD
* _approve_: Approves the Pancakeswap pair contract to spend your *target token*
* _approve BUSD_: Approves the Pancakeswap pair contract to spend your BUSD
* _allowance_: Shows if the Pancakeswap pair can spend your *target token*
* _allowance BUSD_: Shows if the Pancakeswap pair can spend your BUSD
* _gas [GAS]_: Set the gas price for swaps to GAS
* _slippage [SLIPPAGE]_: Set the slippage for swaps to SLIPPAGE percent
* _sell-percentage [PERCENTAGE]_: Sets the amount of *target token* to be sold to *PERCENTAGE* percent of its total amount at the time this command is executed. I.e. if you don' have the token when executing this command, the amount to be sold will remain "0" always.
* _sell-amount [AMOUNT]_: Sets the amount to sell of *target token* to AMOUNT
