# deribit-wrapper

## Overview

This Python script provides a comprehensive client for interacting with the [Deribit API](https://docs.deribit.com/).
It encapsulates functionality for both public and private endpoints, covering market data, account information, trading
operations, and more.
It supports both the production and test environments, making it suitable for developers at all stages of application
development.

## Features

- **Environment Switching:** Easily switch between the production and test environments.
- **Market Data Retrieval:** Access to market data including contract sizes, currencies, ticker information, book
  summaries, and historical data.
- **Account Management:** Functionality to authenticate, retrieve account summaries, positions, and transaction logs.
- **Trading Operations:** Support for placing buy and sell orders, including market and limit orders, as well as bulk
  ordering.
- **Utility Functions:** Helper functions to convert timestamps, retrieve specific instruments or markets, and calculate
  margins.

## Installation

Install `deribit-wrapper` using pip:

```bash
pip install deribit-wrapper
```

## Configuration

Instantiate the `DeribitClient` class with the appropriate parameters:

- `client_id`: Your Deribit client ID.
- `client_secret`: Your Deribit client secret.
- `simulated`: Set to `True` to use the test environment or `False` to use the production environment.
- `env`: Choose between `'test'` and `'prod'` environments. Defaults to `'prod'`.

Example:

```python
from deribit_wrapper import DeribitClient

client = DeribitClient(client_id='your_client_id', client_secret='your_client_secret')
```

## Usage

### Market Data

- **Get Contract Size:** `get_contract_size(asset)`
- **Get Currencies:** `get_currencies()`
- **Get Ticker Information:** `get_ticker(asset)`
- **Get Book Summary by Currency:** `get_complete_market_book()`
- and more...

### Account Information

- **Authenticate:** Automatically handled during requests to private endpoints.
- **Get Account Summary:** `get_account_summary(currency)`
- **Get Positions:** `get_positions(currency, kind)`
- and more...

### Trading

- **Place an Order:** `order(asset, amount, limit=None, label=None, reduce_only=False)`
- **Place a Market Order:** `market_order(asset, amount, label=None, reduce_only=False)`
- **Bulk Orders:** `bulk_order(orders, label=None)`
- and more...

## Examples

1. **Retrieving Market Data:**

```python
ticker_info = client.get_ticker('BTC-25JUN21')
print(ticker_info)
```

2. **Placing a Market Order:**

```python
order_response = client.market_order('BTC-25JUN21', 1)
print(order_response)
```

3. **Getting Account Summary:**

```python
account_summary = client.get_account_summary('BTC')
print(account_summary)
```

## Getting Help

If you encounter any issues or have questions about using `deribit-wrapper`,
please create an issue in the [GitHub repository](https://github.com/AntonioVentilii/deribit-wrapper/issues).

## Contributing

Contributions to `deribit-wrapper` are welcome!
Whether it's bug reports, feature requests, or code contributions, please feel free to make a contribution. For code
contributions, please:

1. Fork the repository.
2. Create a new branch for your feature or fix.
3. Submit a pull request.

Please ensure your code adheres to the project's coding standards and includes appropriate tests.

## License

`deribit-wrapper` is released under the MIT License. See the LICENSE file for more details.
