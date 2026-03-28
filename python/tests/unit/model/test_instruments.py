# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------

from decimal import Decimal

from nautilus_trader.model import CryptoPerpetual
from nautilus_trader.model import Currency
from nautilus_trader.model import CurrencyPair
from nautilus_trader.model import Equity
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import Symbol
from nautilus_trader.model import Venue
from tests.providers import TestInstrumentProviderV2


def test_audusd_sim_construction():
    audusd = TestInstrumentProviderV2.audusd_sim()

    assert audusd.id == InstrumentId(Symbol("AUD/USD"), Venue("SIM"))
    assert audusd.base_currency == Currency.from_str("AUD")
    assert audusd.quote_currency == Currency.from_str("USD")
    assert audusd.price_precision == 5
    assert audusd.size_precision == 0


def test_usdjpy_sim_construction():
    usdjpy = TestInstrumentProviderV2.usdjpy_sim()

    assert usdjpy.id == InstrumentId(Symbol("USD/JPY"), Venue("SIM"))
    assert usdjpy.base_currency == Currency.from_str("USD")
    assert usdjpy.quote_currency == Currency.from_str("JPY")
    assert usdjpy.price_precision == 3
    assert usdjpy.size_precision == 0


def test_ethusdt_binance_construction():
    ethusdt = TestInstrumentProviderV2.ethusdt_binance()

    assert ethusdt.id == InstrumentId(Symbol("ETHUSDT"), Venue("BINANCE"))
    assert ethusdt.base_currency == Currency.from_str("ETH")
    assert ethusdt.quote_currency == Currency.from_str("USDT")
    assert ethusdt.price_precision == 2
    assert ethusdt.size_precision == 5


def test_btcusdt_binance_construction():
    btcusdt = TestInstrumentProviderV2.btcusdt_binance()

    assert btcusdt.id == InstrumentId(Symbol("BTCUSDT"), Venue("BINANCE"))
    assert btcusdt.base_currency == Currency.from_str("BTC")
    assert btcusdt.quote_currency == Currency.from_str("USDT")
    assert btcusdt.price_precision == 2
    assert btcusdt.size_precision == 6


def test_currency_pair_hash():
    audusd = TestInstrumentProviderV2.audusd_sim()
    assert isinstance(hash(audusd), int)


def test_currency_pair_type_name():
    audusd = TestInstrumentProviderV2.audusd_sim()
    assert audusd.type_name == "CurrencyPair"


def test_currency_pair_properties():
    audusd = TestInstrumentProviderV2.audusd_sim()

    assert audusd.price_increment == Price(1e-05, precision=5)
    assert audusd.size_increment == Quantity.from_int(1)
    assert audusd.lot_size == Quantity.from_str("1000")
    assert audusd.max_quantity == Quantity.from_str("1e7")
    assert audusd.min_quantity == Quantity.from_str("1000")
    assert audusd.margin_init == Decimal("0.03")
    assert audusd.margin_maint == Decimal("0.03")
    assert audusd.maker_fee == Decimal("0.00002")
    assert audusd.taker_fee == Decimal("0.00002")


def test_currency_pair_to_dict_and_from_dict_roundtrip():
    audusd = TestInstrumentProviderV2.audusd_sim()
    d = audusd.to_dict()
    restored = CurrencyPair.from_dict(d)

    assert restored.id == audusd.id
    assert restored.base_currency == audusd.base_currency
    assert restored.quote_currency == audusd.quote_currency
    assert restored.price_precision == audusd.price_precision
    assert restored.size_precision == audusd.size_precision


def test_currency_pair_direct_construction():
    pair = CurrencyPair(
        instrument_id=InstrumentId(Symbol("TEST/USD"), Venue("SIM")),
        raw_symbol=Symbol("TEST/USD"),
        base_currency=Currency.from_str("BTC"),
        quote_currency=Currency.from_str("USD"),
        price_precision=2,
        size_precision=6,
        price_increment=Price(0.01, precision=2),
        size_increment=Quantity(0.000001, precision=6),
        ts_event=0,
        ts_init=0,
    )

    assert pair.id == InstrumentId(Symbol("TEST/USD"), Venue("SIM"))
    assert pair.price_precision == 2
    assert pair.size_precision == 6


def test_btcusdt_perp_construction():
    perp = TestInstrumentProviderV2.btcusdt_perp_binance()

    assert perp.id == InstrumentId(Symbol("BTCUSDT-PERP"), Venue("BINANCE"))
    assert perp.base_currency == Currency.from_str("BTC")
    assert perp.quote_currency == Currency.from_str("USDT")
    assert perp.settlement_currency == Currency.from_str("USDT")
    assert perp.is_inverse is False
    assert perp.price_precision == 1
    assert perp.size_precision == 3


def test_crypto_perpetual_type_name():
    perp = TestInstrumentProviderV2.btcusdt_perp_binance()
    assert perp.type_name == "CryptoPerpetual"


def test_crypto_perpetual_hash():
    perp = TestInstrumentProviderV2.btcusdt_perp_binance()
    assert isinstance(hash(perp), int)


def test_crypto_perpetual_to_dict_and_from_dict_roundtrip():
    perp = TestInstrumentProviderV2.btcusdt_perp_binance()
    d = perp.to_dict()
    restored = CryptoPerpetual.from_dict(d)

    assert restored.id == perp.id
    assert restored.base_currency == perp.base_currency
    assert restored.settlement_currency == perp.settlement_currency
    assert restored.is_inverse == perp.is_inverse
    assert restored.price_precision == perp.price_precision
    assert restored.size_precision == perp.size_precision


def test_crypto_perpetual_direct_construction():
    perp = CryptoPerpetual(
        instrument_id=InstrumentId(Symbol("ETHUSDT-PERP"), Venue("BINANCE")),
        raw_symbol=Symbol("ETHUSDT"),
        base_currency=Currency.from_str("ETH"),
        quote_currency=Currency.from_str("USDT"),
        settlement_currency=Currency.from_str("USDT"),
        is_inverse=False,
        price_precision=2,
        size_precision=3,
        price_increment=Price.from_str("0.01"),
        size_increment=Quantity.from_str("0.001"),
        ts_event=0,
        ts_init=0,
    )

    assert perp.id == InstrumentId(Symbol("ETHUSDT-PERP"), Venue("BINANCE"))
    assert perp.is_inverse is False


def test_equity_direct_construction():
    equity = Equity(
        instrument_id=InstrumentId(Symbol("AAPL"), Venue("NASDAQ")),
        raw_symbol=Symbol("AAPL"),
        currency=Currency.from_str("USD"),
        price_precision=2,
        price_increment=Price.from_str("0.01"),
        ts_event=0,
        ts_init=0,
        isin="US0378331005",
    )

    assert equity.id == InstrumentId(Symbol("AAPL"), Venue("NASDAQ"))
    assert equity.type_name == "Equity"
    assert equity.quote_currency == Currency.from_str("USD")
    assert equity.price_precision == 2


def test_equity_to_dict_and_from_dict_roundtrip():
    equity = Equity(
        instrument_id=InstrumentId(Symbol("AAPL"), Venue("NASDAQ")),
        raw_symbol=Symbol("AAPL"),
        currency=Currency.from_str("USD"),
        price_precision=2,
        price_increment=Price.from_str("0.01"),
        ts_event=0,
        ts_init=0,
    )

    d = equity.to_dict()
    restored = Equity.from_dict(d)

    assert restored.id == equity.id
    assert restored.quote_currency == equity.quote_currency
    assert restored.price_precision == equity.price_precision
