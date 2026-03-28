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

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from nautilus_trader.model import CryptoPerpetual
from nautilus_trader.model import Currency
from nautilus_trader.model import CurrencyPair
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Money
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import QuoteTick
from nautilus_trader.model import Symbol
from nautilus_trader.model import Venue


PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_DATA_DIR = PACKAGE_ROOT / "tests" / "test_data"


class TestInstrumentProviderV2:
    """
    Factory methods for common test instruments using v2 model types.
    """

    @staticmethod
    def default_fx_ccy(symbol: str, venue: Venue | None = None) -> CurrencyPair:
        if venue is None:
            venue = Venue("SIM")

        base_currency = symbol[:3]
        quote_currency = symbol[-3:]

        if quote_currency == "JPY":
            price_precision = 3
        else:
            price_precision = 5

        return CurrencyPair(
            instrument_id=InstrumentId(Symbol(symbol), venue),
            raw_symbol=Symbol(symbol),
            base_currency=Currency.from_str(base_currency),
            quote_currency=Currency.from_str(quote_currency),
            price_precision=price_precision,
            size_precision=0,
            price_increment=Price(1 / 10**price_precision, price_precision),
            size_increment=Quantity.from_int(1),
            ts_event=0,
            ts_init=0,
            lot_size=Quantity.from_str("1000"),
            max_quantity=Quantity.from_str("1e7"),
            min_quantity=Quantity.from_str("1000"),
            max_notional=Money(50_000_000.00, Currency.from_str("USD")),
            min_notional=Money(1_000.00, Currency.from_str("USD")),
            margin_init=Decimal("0.03"),
            margin_maint=Decimal("0.03"),
            maker_fee=Decimal("0.00002"),
            taker_fee=Decimal("0.00002"),
        )

    @staticmethod
    def audusd_sim() -> CurrencyPair:
        return TestInstrumentProviderV2.default_fx_ccy("AUD/USD")

    @staticmethod
    def usdjpy_sim() -> CurrencyPair:
        return TestInstrumentProviderV2.default_fx_ccy("USD/JPY")

    @staticmethod
    def gbpusd_sim() -> CurrencyPair:
        return TestInstrumentProviderV2.default_fx_ccy("GBP/USD")

    @staticmethod
    def ethusdt_binance() -> CurrencyPair:
        return CurrencyPair(
            instrument_id=InstrumentId(Symbol("ETHUSDT"), Venue("BINANCE")),
            raw_symbol=Symbol("ETHUSDT"),
            base_currency=Currency.from_str("ETH"),
            quote_currency=Currency.from_str("USDT"),
            price_precision=2,
            size_precision=5,
            price_increment=Price(1e-02, precision=2),
            size_increment=Quantity(1e-05, precision=5),
            ts_event=0,
            ts_init=0,
            max_quantity=Quantity(9000, precision=5),
            min_quantity=Quantity(1e-05, precision=5),
            min_notional=Money(10.00, Currency.from_str("USDT")),
            max_price=Price(1000000, precision=2),
            min_price=Price(0.01, precision=2),
            margin_init=Decimal("1.00"),
            margin_maint=Decimal("0.35"),
            maker_fee=Decimal("0.0001"),
            taker_fee=Decimal("0.0001"),
        )

    @staticmethod
    def btcusdt_binance() -> CurrencyPair:
        return CurrencyPair(
            instrument_id=InstrumentId(Symbol("BTCUSDT"), Venue("BINANCE")),
            raw_symbol=Symbol("BTCUSDT"),
            base_currency=Currency.from_str("BTC"),
            quote_currency=Currency.from_str("USDT"),
            price_precision=2,
            size_precision=6,
            price_increment=Price(1e-02, precision=2),
            size_increment=Quantity(1e-06, precision=6),
            ts_event=0,
            ts_init=0,
            max_quantity=Quantity(9000, precision=6),
            min_quantity=Quantity(1e-06, precision=6),
            min_notional=Money(10.00, Currency.from_str("USDT")),
            max_price=Price(1000000, precision=2),
            min_price=Price(0.01, precision=2),
            margin_init=Decimal(0),
            margin_maint=Decimal(0),
            maker_fee=Decimal("0.001"),
            taker_fee=Decimal("0.001"),
        )

    @staticmethod
    def btcusdt_perp_binance() -> CryptoPerpetual:
        return CryptoPerpetual(
            instrument_id=InstrumentId(Symbol("BTCUSDT-PERP"), Venue("BINANCE")),
            raw_symbol=Symbol("BTCUSDT"),
            base_currency=Currency.from_str("BTC"),
            quote_currency=Currency.from_str("USDT"),
            settlement_currency=Currency.from_str("USDT"),
            is_inverse=False,
            price_precision=1,
            size_precision=3,
            price_increment=Price.from_str("0.1"),
            size_increment=Quantity.from_str("0.001"),
            ts_event=0,
            ts_init=0,
            max_quantity=Quantity.from_str("1000.000"),
            min_quantity=Quantity.from_str("0.001"),
            min_notional=Money(10.00, Currency.from_str("USDT")),
            max_price=Price.from_str("809484.0"),
            min_price=Price.from_str("261.1"),
            margin_init=Decimal("0.0500"),
            margin_maint=Decimal("0.0250"),
            maker_fee=Decimal("0.000200"),
            taker_fee=Decimal("0.000180"),
        )


class TestDataProviderV2:
    """
    Load test data from CSV/Parquet files in tests/test_data/.
    """

    @staticmethod
    def usdjpy_quotes_from_parquet() -> list[QuoteTick]:
        """
        Load USD/JPY quote ticks from the Parquet test data file.
        """
        from nautilus_trader.persistence import DataBackendSession
        from nautilus_trader.persistence import NautilusDataType

        path = str(TEST_DATA_DIR / "quote_tick_usdjpy_2019_sim_rust.parquet")
        session = DataBackendSession().new_session()
        session.add_file(NautilusDataType.QuoteTick, "quote_ticks", path)
        result = session.to_query_result()
        ticks = []
        for batch in result:
            if batch is not None:
                ticks.extend(batch)
        return ticks

    @staticmethod
    def eurusd_quotes_from_parquet() -> list[QuoteTick]:
        """
        Load EUR/USD quote ticks from the Parquet test data file.
        """
        from nautilus_trader.persistence import DataBackendSession
        from nautilus_trader.persistence import NautilusDataType

        path = str(TEST_DATA_DIR / "quote_tick_eurusd_2019_sim_rust.parquet")
        session = DataBackendSession().new_session()
        session.add_file(NautilusDataType.QuoteTick, "quote_ticks", path)
        result = session.to_query_result()
        ticks = []
        for batch in result:
            if batch is not None:
                ticks.extend(batch)
        return ticks
