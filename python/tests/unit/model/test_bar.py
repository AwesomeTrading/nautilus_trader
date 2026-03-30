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

from datetime import timedelta

import pytest

from nautilus_trader.model import AggregationSource
from nautilus_trader.model import Bar
from nautilus_trader.model import BarAggregation
from nautilus_trader.model import BarSpecification
from nautilus_trader.model import BarType
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Price
from nautilus_trader.model import PriceType
from nautilus_trader.model import Quantity
from nautilus_trader.model import Symbol
from nautilus_trader.model import Venue


@pytest.fixture
def one_min_bid():
    return BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)


@pytest.fixture
def audusd_1_min_bid(audusd_id, one_min_bid):
    return BarType(audusd_id, one_min_bid)


def test_bar_spec_equality():
    spec1 = BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)
    spec2 = BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)
    spec3 = BarSpecification(1, BarAggregation.MINUTE, PriceType.ASK)

    assert spec1 == spec2
    assert spec1 != spec3


def test_bar_spec_hash_and_str():
    spec = BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)

    assert isinstance(hash(spec), int)
    assert str(spec) == "1-MINUTE-BID"


def test_bar_spec_properties():
    spec = BarSpecification(1, BarAggregation.HOUR, PriceType.BID)

    assert spec.step == 1
    assert spec.aggregation == BarAggregation.HOUR
    assert spec.price_type == PriceType.BID


@pytest.mark.parametrize(
    ("step", "aggregation", "expected_str"),
    [
        (1, BarAggregation.MINUTE, "1-MINUTE-BID"),
        (5, BarAggregation.MINUTE, "5-MINUTE-BID"),
        (100, BarAggregation.TICK, "100-TICK-BID"),
        (1, BarAggregation.HOUR, "1-HOUR-BID"),
        (1, BarAggregation.DAY, "1-DAY-BID"),
    ],
)
def test_bar_spec_str_with_various_aggregations(step, aggregation, expected_str):
    spec = BarSpecification(step, aggregation, PriceType.BID)
    assert str(spec) == expected_str


@pytest.mark.parametrize(
    ("step", "aggregation", "expected"),
    [
        (500, BarAggregation.MILLISECOND, timedelta(milliseconds=500)),
        (10, BarAggregation.SECOND, timedelta(seconds=10)),
        (5, BarAggregation.MINUTE, timedelta(minutes=5)),
        (1, BarAggregation.HOUR, timedelta(hours=1)),
        (1, BarAggregation.DAY, timedelta(days=1)),
    ],
)
def test_bar_spec_timedelta(step, aggregation, expected):
    spec = BarSpecification(step, aggregation, PriceType.LAST)

    assert spec.timedelta == expected


def test_bar_type_equality(audusd_id, one_min_bid):
    bt1 = BarType(audusd_id, one_min_bid)
    bt2 = BarType(audusd_id, one_min_bid)
    bt3 = BarType(InstrumentId(Symbol("GBP/USD"), Venue("SIM")), one_min_bid)

    assert bt1 == bt2
    assert bt1 != bt3


def test_bar_type_hash(audusd_id, one_min_bid):
    bt = BarType(audusd_id, one_min_bid)
    assert isinstance(hash(bt), int)


def test_bar_type_str(audusd_id, one_min_bid):
    bt = BarType(audusd_id, one_min_bid)

    assert str(bt) == "AUD/USD.SIM-1-MINUTE-BID-EXTERNAL"


def test_bar_type_from_str(audusd_id):
    bar_type = BarType.from_str("AUD/USD.SIM-1-MINUTE-BID-INTERNAL")

    assert bar_type.spec.step == 1
    assert bar_type.spec.aggregation == BarAggregation.MINUTE
    assert bar_type.spec.price_type == PriceType.BID


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (
            "AUD/USD.IDEALPRO-1-MINUTE-BID-EXTERNAL",
            BarType(
                InstrumentId(Symbol("AUD/USD"), Venue("IDEALPRO")),
                BarSpecification(1, BarAggregation.MINUTE, PriceType.BID),
            ),
        ),
        (
            "GBP/USD.SIM-1000-TICK-MID-INTERNAL",
            BarType(
                InstrumentId(Symbol("GBP/USD"), Venue("SIM")),
                BarSpecification(1000, BarAggregation.TICK, PriceType.MID),
                AggregationSource.INTERNAL,
            ),
        ),
        (
            "AAPL.NYSE-1-HOUR-MID-INTERNAL",
            BarType(
                InstrumentId(Symbol("AAPL"), Venue("NYSE")),
                BarSpecification(1, BarAggregation.HOUR, PriceType.MID),
                AggregationSource.INTERNAL,
            ),
        ),
        (
            "ETHUSDT-PERP.BINANCE-100-TICK-LAST-INTERNAL",
            BarType(
                InstrumentId(Symbol("ETHUSDT-PERP"), Venue("BINANCE")),
                BarSpecification(100, BarAggregation.TICK, PriceType.LAST),
                AggregationSource.INTERNAL,
            ),
        ),
    ],
)
def test_bar_type_from_str_valid(value, expected):
    assert BarType.from_str(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", "AUD/USD", "AUD/USD.IDEALPRO-1-MILLISECOND-BID"],
)
def test_bar_type_from_str_invalid(value):
    with pytest.raises(ValueError, match="Error parsing"):
        BarType.from_str(value)


def test_bar_type_from_str_with_utf8():
    bar_type = BarType.from_str("TËST-PÉRP.BINANCE-1-MINUTE-LAST-EXTERNAL")

    assert bar_type.spec == BarSpecification(1, BarAggregation.MINUTE, PriceType.LAST)
    assert str(bar_type) == "TËST-PÉRP.BINANCE-1-MINUTE-LAST-EXTERNAL"


def test_bar_type_composite():
    bt = BarType.from_str("BTCUSDT-PERP.BINANCE-2-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL")

    assert bt.is_composite()
    assert str(bt) == "BTCUSDT-PERP.BINANCE-2-MINUTE-LAST-INTERNAL@1-MINUTE-EXTERNAL"

    std = bt.standard()
    assert std.is_standard()
    assert str(std) == "BTCUSDT-PERP.BINANCE-2-MINUTE-LAST-INTERNAL"

    comp = bt.composite()
    assert comp.is_standard()
    assert str(comp) == "BTCUSDT-PERP.BINANCE-1-MINUTE-LAST-EXTERNAL"


def test_bar_fully_qualified_name():
    assert Bar.fully_qualified_name() == "nautilus_trader.core.nautilus_pyo3.model:Bar"


def test_bar_construction(audusd_1_min_bid):
    bar = Bar(
        bar_type=audusd_1_min_bid,
        open=Price.from_str("1.00001"),
        high=Price.from_str("1.00010"),
        low=Price.from_str("1.00000"),
        close=Price.from_str("1.00002"),
        volume=Quantity.from_int(100_000),
        ts_event=1,
        ts_init=2,
    )

    assert bar.bar_type == audusd_1_min_bid
    assert bar.open == Price.from_str("1.00001")
    assert bar.high == Price.from_str("1.00010")
    assert bar.low == Price.from_str("1.00000")
    assert bar.close == Price.from_str("1.00002")
    assert bar.volume == Quantity.from_int(100_000)
    assert bar.ts_event == 1
    assert bar.ts_init == 2


def test_bar_equality(audusd_1_min_bid):
    bar1 = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00001"),
        Price.from_str("1.00004"),
        Price.from_str("1.00001"),
        Price.from_str("1.00001"),
        Quantity.from_int(100_000),
        0,
        0,
    )
    bar2 = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00000"),
        Price.from_str("1.00004"),
        Price.from_str("1.00000"),
        Price.from_str("1.00003"),
        Quantity.from_int(100_000),
        0,
        0,
    )

    assert bar1 == bar1
    assert bar1 != bar2


def test_bar_hash(audusd_1_min_bid):
    bar = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00001"),
        Price.from_str("1.00010"),
        Price.from_str("1.00000"),
        Price.from_str("1.00002"),
        Quantity.from_int(100_000),
        0,
        0,
    )

    assert isinstance(hash(bar), int)


def test_bar_str(audusd_1_min_bid):
    bar = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00001"),
        Price.from_str("1.00004"),
        Price.from_str("1.00000"),
        Price.from_str("1.00003"),
        Quantity.from_int(100_000),
        0,
        0,
    )

    assert str(bar) == "AUD/USD.SIM-1-MINUTE-BID-EXTERNAL,1.00001,1.00004,1.00000,1.00003,100000,0"


def test_bar_validation_high_below_open(audusd_1_min_bid):
    with pytest.raises(ValueError, match="high >= open"):
        Bar(
            audusd_1_min_bid,
            Price.from_str("1.00001"),
            Price.from_str("1.00000"),
            Price.from_str("1.00000"),
            Price.from_str("1.00000"),
            Quantity.from_int(100_000),
            0,
            0,
        )


def test_bar_validation_high_below_low(audusd_1_min_bid):
    with pytest.raises(ValueError, match="high >= open"):
        Bar(
            audusd_1_min_bid,
            Price.from_str("1.00001"),
            Price.from_str("1.00000"),
            Price.from_str("1.00002"),
            Price.from_str("1.00003"),
            Quantity.from_int(100_000),
            0,
            0,
        )


def test_bar_validation_high_below_close(audusd_1_min_bid):
    with pytest.raises(ValueError, match="high >= close"):
        Bar(
            audusd_1_min_bid,
            Price.from_str("1.00000"),
            Price.from_str("1.00000"),
            Price.from_str("1.00000"),
            Price.from_str("1.00001"),
            Quantity.from_int(100_000),
            0,
            0,
        )


def test_bar_validation_low_above_open(audusd_1_min_bid):
    with pytest.raises(ValueError, match="low <= open"):
        Bar(
            audusd_1_min_bid,
            Price.from_str("0.99999"),
            Price.from_str("1.00000"),
            Price.from_str("1.00000"),
            Price.from_str("1.00000"),
            Quantity.from_int(100_000),
            0,
            0,
        )


def test_bar_validation_low_above_close(audusd_1_min_bid):
    with pytest.raises(ValueError, match="low <= close"):
        Bar(
            audusd_1_min_bid,
            Price.from_str("1.00000"),
            Price.from_str("1.00005"),
            Price.from_str("1.00000"),
            Price.from_str("0.99999"),
            Quantity.from_int(100_000),
            0,
            0,
        )


def test_bar_to_dict(audusd_1_min_bid):
    bar = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00001"),
        Price.from_str("1.00004"),
        Price.from_str("1.00000"),
        Price.from_str("1.00003"),
        Quantity.from_int(100_000),
        0,
        0,
    )

    assert bar.to_dict() == {
        "type": "Bar",
        "bar_type": "AUD/USD.SIM-1-MINUTE-BID-EXTERNAL",
        "open": "1.00001",
        "high": "1.00004",
        "low": "1.00000",
        "close": "1.00003",
        "volume": "100000",
        "ts_event": 0,
        "ts_init": 0,
    }


def test_bar_from_dict_roundtrip(audusd_1_min_bid):
    bar = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00001"),
        Price.from_str("1.00010"),
        Price.from_str("1.00000"),
        Price.from_str("1.00002"),
        Quantity.from_int(100_000),
        1,
        2,
    )

    restored = Bar.from_dict(bar.to_dict())

    assert restored == bar
