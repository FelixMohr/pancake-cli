def info(s: str):
    print(" 🥞    {}".format(s))


def set_decimals(number, decimals):
    number = str(number)
    split = number.split('.')
    number_absolute = split[0]
    number_decimals = ''
    if len(split) > 1:
        number_decimals = split[1]
    if len(number_decimals) < decimals:
        number_decimals = number_decimals + ''.join(["0" for _ in range(decimals - len(number_decimals))])
    return int(number_absolute + number_decimals)
