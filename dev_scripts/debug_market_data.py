from deribit_wrapper.market_data import MarketData

# This script is used to debug the market data class.
# It doesn't require the CLIENT_ID and CLIENT_SECRET to be set in the environment since it only uses public endpoints.
# It can be used in the production environment as well.

USE_TEST_ENV = True

md_test = MarketData(env='test')
md_prod = MarketData()

if USE_TEST_ENV:
    md = md_test
else:
    md = md_prod

CURRENCY = 'MATIC'


def debug_get_currencies():
    currencies = md.currencies
    print(f'Currencies: {currencies}')


def debug_get_instruments():
    currency = CURRENCY
    instruments = md.get_instruments(currency, as_list=True)
    print(f'Instruments for {currency}: {instruments}')


def debug_get_first_future():
    currency = CURRENCY
    future = md.get_first_future(currency)
    print(f'First future for {currency}: {future}')


def run():
    debug_get_currencies()
    debug_get_instruments()
    debug_get_first_future()


if __name__ == "__main__":
    run()
