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

from nautilus_trader.model import DataType
from nautilus_trader.model import FundingRateUpdate
from nautilus_trader.model import InstrumentClose
from nautilus_trader.model import InstrumentCloseType
from nautilus_trader.model import InstrumentStatus
from nautilus_trader.model import MarketStatusAction
from nautilus_trader.model import MarkPriceUpdate
from nautilus_trader.model import Price


def test_data_type_construction():
    dt = DataType("QuoteTick", metadata={"instrument_id": "AUD/USD.SIM"})

    assert dt.type_name == "QuoteTick"
    assert dt.metadata == {"instrument_id": "AUD/USD.SIM"}


def test_data_type_equality():
    dt1 = DataType("QuoteTick", metadata={"instrument_id": "AUD/USD.SIM"})
    dt2 = DataType("QuoteTick", metadata={"instrument_id": "AUD/USD.SIM"})
    dt3 = DataType("QuoteTick", metadata={"instrument_id": "GBP/USD.SIM"})

    assert dt1 == dt2
    assert dt1 != dt3


def test_data_type_hash():
    dt1 = DataType("QuoteTick", metadata={"instrument_id": "AUD/USD.SIM"})
    dt2 = DataType("QuoteTick", metadata={"instrument_id": "AUD/USD.SIM"})

    assert hash(dt1) == hash(dt2)


def test_data_type_topic():
    dt = DataType("QuoteTick", metadata={"instrument_id": "AUD/USD.SIM"})

    assert "QuoteTick" in dt.topic
    assert "AUD/USD.SIM" in dt.topic


def test_instrument_status_construction(audusd_id):
    status = InstrumentStatus(
        instrument_id=audusd_id,
        action=MarketStatusAction.TRADING,
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
        reason="Session open",
        trading_event="open",
        is_trading=True,
        is_quoting=True,
        is_short_sell_restricted=False,
    )

    assert status.instrument_id == audusd_id
    assert status.action == MarketStatusAction.TRADING
    assert status.ts_event == 1_000_000_000
    assert status.ts_init == 1_000_000_001
    assert status.reason == "Session open"
    assert status.trading_event == "open"
    assert status.is_trading is True
    assert status.is_quoting is True
    assert status.is_short_sell_restricted is False


def test_instrument_status_equality(audusd_id):
    s1 = InstrumentStatus(audusd_id, MarketStatusAction.TRADING, 0, 0)
    s2 = InstrumentStatus(audusd_id, MarketStatusAction.TRADING, 0, 0)

    assert s1 == s2


def test_instrument_status_repr(audusd_id):
    status = InstrumentStatus(audusd_id, MarketStatusAction.TRADING, 0, 0)
    r = repr(status)

    assert "InstrumentStatus" in r
    assert "AUD/USD.SIM" in r
    assert "TRADING" in r


def test_instrument_status_to_dict_and_from_dict_roundtrip(audusd_id):
    status = InstrumentStatus(
        instrument_id=audusd_id,
        action=MarketStatusAction.TRADING,
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
        reason="Session open",
        trading_event="open",
        is_trading=True,
        is_quoting=True,
        is_short_sell_restricted=False,
    )

    d = InstrumentStatus.to_dict(status)
    restored = InstrumentStatus.from_dict(d)

    assert d["type"] == "InstrumentStatus"
    assert restored == status


def test_instrument_close_construction(audusd_id):
    close = InstrumentClose(
        instrument_id=audusd_id,
        close_price=Price.from_str("0.75000"),
        close_type=InstrumentCloseType.END_OF_SESSION,
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
    )

    assert close.instrument_id == audusd_id
    assert close.close_price == Price.from_str("0.75000")
    assert close.close_type == InstrumentCloseType.END_OF_SESSION
    assert close.ts_event == 1_000_000_000
    assert close.ts_init == 1_000_000_001


def test_instrument_close_equality(audusd_id):
    c1 = InstrumentClose(
        audusd_id,
        Price.from_str("0.75000"),
        InstrumentCloseType.END_OF_SESSION,
        0,
        0,
    )
    c2 = InstrumentClose(
        audusd_id,
        Price.from_str("0.75000"),
        InstrumentCloseType.END_OF_SESSION,
        0,
        0,
    )

    assert c1 == c2


def test_instrument_close_repr(audusd_id):
    close = InstrumentClose(
        audusd_id,
        Price.from_str("0.75000"),
        InstrumentCloseType.END_OF_SESSION,
        0,
        0,
    )
    r = repr(close)

    assert "0.75000" in r
    assert "END_OF_SESSION" in r


def test_instrument_close_to_dict_and_from_dict_roundtrip(audusd_id):
    close = InstrumentClose(
        instrument_id=audusd_id,
        close_price=Price.from_str("0.75000"),
        close_type=InstrumentCloseType.END_OF_SESSION,
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
    )

    d = InstrumentClose.to_dict(close)
    restored = InstrumentClose.from_dict(d)

    assert d["type"] == "InstrumentClose"
    assert restored == close


def test_mark_price_update_construction(audusd_id):
    mark = MarkPriceUpdate(
        instrument_id=audusd_id,
        value=Price.from_str("50000.00"),
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
    )

    assert mark.instrument_id == audusd_id
    assert mark.value == Price.from_str("50000.00")
    assert mark.ts_event == 1_000_000_000
    assert mark.ts_init == 1_000_000_001


def test_mark_price_update_equality(audusd_id):
    m1 = MarkPriceUpdate(audusd_id, Price.from_str("50000.00"), 0, 0)
    m2 = MarkPriceUpdate(audusd_id, Price.from_str("50000.00"), 0, 0)

    assert m1 == m2


def test_mark_price_update_hash(audusd_id):
    m1 = MarkPriceUpdate(audusd_id, Price.from_str("50000.00"), 0, 0)
    m2 = MarkPriceUpdate(audusd_id, Price.from_str("50000.00"), 0, 0)

    assert hash(m1) == hash(m2)


def test_mark_price_update_str_and_repr(audusd_id):
    mark = MarkPriceUpdate(audusd_id, Price.from_str("50000.00"), 0, 0)

    assert "50000.00" in str(mark)
    assert "MarkPriceUpdate" in repr(mark)


def test_mark_price_update_to_dict_and_from_dict_roundtrip(audusd_id):
    mark = MarkPriceUpdate(
        instrument_id=audusd_id,
        value=Price.from_str("50000.00"),
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
    )

    d = MarkPriceUpdate.to_dict(mark)
    restored = MarkPriceUpdate.from_dict(d)

    assert d["type"] == "MarkPriceUpdate"
    assert restored == mark


def test_funding_rate_update_construction(audusd_id):
    funding = FundingRateUpdate(
        instrument_id=audusd_id,
        rate=Decimal("0.0001"),
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
        interval=480,
        next_funding_ns=2_000_000_000,
    )

    assert funding.instrument_id == audusd_id
    assert funding.rate == Decimal("0.0001")
    assert funding.interval == 480
    assert funding.next_funding_ns == 2_000_000_000
    assert funding.ts_event == 1_000_000_000
    assert funding.ts_init == 1_000_000_001


def test_funding_rate_update_equality(audusd_id):
    f1 = FundingRateUpdate(audusd_id, Decimal("0.0001"), 0, 0, interval=480)
    f2 = FundingRateUpdate(audusd_id, Decimal("0.0001"), 0, 0, interval=480)

    assert f1 == f2


def test_funding_rate_update_hash(audusd_id):
    f1 = FundingRateUpdate(audusd_id, Decimal("0.0001"), 0, 0, interval=480)
    f2 = FundingRateUpdate(audusd_id, Decimal("0.0001"), 0, 0, interval=480)

    assert hash(f1) == hash(f2)


def test_funding_rate_update_repr(audusd_id):
    funding = FundingRateUpdate(audusd_id, Decimal("0.0001"), 0, 0)
    r = repr(funding)

    assert "FundingRateUpdate" in r
    assert "AUD/USD.SIM" in r
    assert "0.0001" in r


def test_funding_rate_update_to_dict_and_from_dict_roundtrip(audusd_id):
    funding = FundingRateUpdate(
        instrument_id=audusd_id,
        rate=Decimal("0.0001"),
        ts_event=1_000_000_000,
        ts_init=1_000_000_001,
        interval=480,
        next_funding_ns=2_000_000_000,
    )

    d = FundingRateUpdate.to_dict(funding)
    restored = FundingRateUpdate.from_dict(d)

    assert d["type"] == "FundingRateUpdate"
    assert restored == funding
