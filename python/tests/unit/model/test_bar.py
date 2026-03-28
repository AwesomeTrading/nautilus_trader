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

import pickle

import pytest

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
def audusd_sim_id():
    return InstrumentId(Symbol("AUD/USD"), Venue("SIM"))


@pytest.fixture
def one_min_bid():
    return BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)


@pytest.fixture
def audusd_1_min_bid(audusd_sim_id, one_min_bid):
    return BarType(audusd_sim_id, one_min_bid)


def test_bar_spec_equality():
    spec1 = BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)
    spec2 = BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)
    spec3 = BarSpecification(1, BarAggregation.MINUTE, PriceType.ASK)

    assert spec1 == spec2
    assert spec1 != spec3


@pytest.mark.skip(reason="WIP: v2 BarSpecification repr differs from v1 format")
def test_bar_spec_hash_str_and_repr():
    spec = BarSpecification(1, BarAggregation.MINUTE, PriceType.BID)

    assert isinstance(hash(spec), int)
    assert str(spec) == "1-MINUTE-BID"
    assert repr(spec) == "BarSpecification(1-MINUTE-BID)"


@pytest.mark.skip(reason="WIP: v2 BarSpecification has no from_str yet")
def test_bar_spec_from_str():
    spec = BarSpecification.from_str("5-MINUTE-MID")

    assert spec.step == 5
    assert spec.aggregation == BarAggregation.MINUTE
    assert spec.price_type == PriceType.MID


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


@pytest.mark.skip(reason="WIP: v2 BarSpecification does not support pickle yet")
def test_bar_spec_pickle_roundtrip():
    spec = BarSpecification(1000, BarAggregation.TICK, PriceType.LAST)
    pickled = pickle.dumps(spec)
    unpickled = pickle.loads(pickled)  # noqa: S301

    assert unpickled == spec


@pytest.mark.skip(reason="WIP: v2 BarType is an enum, instrument_id access differs")
def test_bar_type_construction(audusd_sim_id, one_min_bid):
    bar_type = BarType(audusd_sim_id, one_min_bid)

    assert bar_type.instrument_id == audusd_sim_id
    assert bar_type.spec == one_min_bid


def test_bar_type_from_str(audusd_sim_id):
    bar_type = BarType.from_str("AUD/USD.SIM-1-MINUTE-BID-INTERNAL")

    assert bar_type.instrument_id == audusd_sim_id
    assert bar_type.spec.step == 1
    assert bar_type.spec.aggregation == BarAggregation.MINUTE
    assert bar_type.spec.price_type == PriceType.BID


def test_bar_type_equality(audusd_sim_id, one_min_bid):
    bt1 = BarType(audusd_sim_id, one_min_bid)
    bt2 = BarType(audusd_sim_id, one_min_bid)

    assert bt1 == bt2


def test_bar_type_hash(audusd_sim_id, one_min_bid):
    bt = BarType(audusd_sim_id, one_min_bid)
    assert isinstance(hash(bt), int)


@pytest.mark.skip(reason="WIP: v2 BarType does not support pickle yet")
def test_bar_type_pickle_roundtrip(audusd_sim_id, one_min_bid):
    bt = BarType(audusd_sim_id, one_min_bid)
    pickled = pickle.dumps(bt)
    unpickled = pickle.loads(pickled)  # noqa: S301

    assert unpickled == bt


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
        Price.from_str("1.00010"),
        Price.from_str("1.00000"),
        Price.from_str("1.00002"),
        Quantity.from_int(100_000),
        0,
        0,
    )
    bar2 = Bar(
        audusd_1_min_bid,
        Price.from_str("1.00001"),
        Price.from_str("1.00010"),
        Price.from_str("1.00000"),
        Price.from_str("1.00002"),
        Quantity.from_int(100_000),
        0,
        0,
    )

    assert bar1 == bar2


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


def test_bar_to_dict_and_from_dict_roundtrip(audusd_1_min_bid):
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

    d = bar.to_dict()
    restored = Bar.from_dict(d)

    assert restored.bar_type == bar.bar_type
    assert restored.open == bar.open
    assert restored.high == bar.high
    assert restored.low == bar.low
    assert restored.close == bar.close
    assert restored.volume == bar.volume
    assert restored.ts_event == bar.ts_event
    assert restored.ts_init == bar.ts_init


@pytest.mark.skip(reason="WIP: v2 Bar does not support pickle yet")
def test_bar_pickle_roundtrip(audusd_1_min_bid):
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

    pickled = pickle.dumps(bar)
    unpickled = pickle.loads(pickled)  # noqa: S301

    assert unpickled == bar
