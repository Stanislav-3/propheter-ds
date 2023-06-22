import re
import decimal


base_currencies_regex = r'(\w+)((USDT)|(ETH)|(BTC)|(USDT))$'


def split_pair(pair):
    result = re.search(base_currencies_regex, pair)
    if not result:
        raise ValueError('Incorrect pair')

    return result.group(1), result.group(2)


# create a new context for this task
ctx = decimal.Context()
ctx.prec = 20


def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')
