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

from nautilus_trader.model import AggressorSide
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import QuoteTick
from nautilus_trader.model import Symbol
from nautilus_trader.model import TradeId
from nautilus_trader.model import TradeTick
from nautilus_trader.model import Venue


@pytest.fixture
def audusd_sim_id():
    return InstrumentId(Symbol("AUD/USD"), Venue("SIM"))


@pytest.fixture
def quote_tick(audusd_sim_id):
    return QuoteTick(
        instrument_id=audusd_sim_id,
        bid_price=Price.from_str("1.00000"),
        ask_price=Price.from_str("1.00001"),
        bid_size=Quantity.from_int(1),
        ask_size=Quantity.from_int(1),
        ts_event=3,
        ts_init=4,
    )


@pytest.fixture
def trade_tick(audusd_sim_id):
    return TradeTick(
        instrument_id=audusd_sim_id,
        price=Price.from_str("1.00001"),
        size=Quantity.from_int(10_000),
        aggressor_side=AggressorSide.BUYER,
        trade_id=TradeId("123456"),
        ts_event=1,
        ts_init=2,
    )


def test_quote_tick_construction(quote_tick, audusd_sim_id):
    assert quote_tick.instrument_id == audusd_sim_id
    assert quote_tick.bid_price == Price.from_str("1.00000")
    assert quote_tick.ask_price == Price.from_str("1.00001")
    assert quote_tick.bid_size == Quantity.from_int(1)
    assert quote_tick.ask_size == Quantity.from_int(1)
    assert quote_tick.ts_event == 3
    assert quote_tick.ts_init == 4


def test_quote_tick_hash_str_and_repr(quote_tick):
    assert isinstance(hash(quote_tick), int)
    assert str(quote_tick) == "AUD/USD.SIM,1.00000,1.00001,1,1,3"
    assert repr(quote_tick) == "QuoteTick(AUD/USD.SIM,1.00000,1.00001,1,1,3)"


def test_quote_tick_equality(audusd_sim_id):
    tick1 = QuoteTick(
        instrument_id=audusd_sim_id,
        bid_price=Price.from_str("1.00000"),
        ask_price=Price.from_str("1.00001"),
        bid_size=Quantity.from_int(1),
        ask_size=Quantity.from_int(1),
        ts_event=0,
        ts_init=0,
    )
    tick2 = QuoteTick(
        instrument_id=audusd_sim_id,
        bid_price=Price.from_str("1.00000"),
        ask_price=Price.from_str("1.00001"),
        bid_size=Quantity.from_int(1),
        ask_size=Quantity.from_int(1),
        ts_event=0,
        ts_init=0,
    )

    assert tick1 == tick2


def test_quote_tick_pickle_roundtrip(quote_tick):
    pickled = pickle.dumps(quote_tick)
    unpickled = pickle.loads(pickled)  # noqa: S301

    assert unpickled == quote_tick
    assert unpickled.instrument_id == quote_tick.instrument_id
    assert unpickled.bid_price == quote_tick.bid_price


def test_quote_tick_to_dict_and_from_dict_roundtrip(audusd_sim_id):
    tick = QuoteTick(
        instrument_id=audusd_sim_id,
        bid_price=Price.from_str("1.00000"),
        ask_price=Price.from_str("1.00001"),
        bid_size=Quantity.from_int(500_000),
        ask_size=Quantity.from_int(800_000),
        ts_event=1,
        ts_init=2,
    )

    d = tick.to_dict()
    restored = QuoteTick.from_dict(d)

    assert restored.instrument_id == tick.instrument_id
    assert restored.bid_price == tick.bid_price
    assert restored.ask_price == tick.ask_price
    assert restored.bid_size == tick.bid_size
    assert restored.ask_size == tick.ask_size
    assert restored.ts_event == tick.ts_event
    assert restored.ts_init == tick.ts_init


def test_trade_tick_construction(trade_tick, audusd_sim_id):
    assert trade_tick.instrument_id == audusd_sim_id
    assert trade_tick.price == Price.from_str("1.00001")
    assert trade_tick.size == Quantity.from_int(10_000)
    assert trade_tick.aggressor_side == AggressorSide.BUYER
    assert trade_tick.trade_id == TradeId("123456")
    assert trade_tick.ts_event == 1
    assert trade_tick.ts_init == 2


def test_trade_tick_hash_str_and_repr(trade_tick):
    assert isinstance(hash(trade_tick), int)
    assert "AUD/USD.SIM" in str(trade_tick)
    assert "TradeTick" in repr(trade_tick)


def test_trade_tick_equality(audusd_sim_id):
    tick1 = TradeTick(
        instrument_id=audusd_sim_id,
        price=Price.from_str("1.00001"),
        size=Quantity.from_int(50_000),
        aggressor_side=AggressorSide.BUYER,
        trade_id=TradeId("123456"),
        ts_event=0,
        ts_init=0,
    )
    tick2 = TradeTick(
        instrument_id=audusd_sim_id,
        price=Price.from_str("1.00001"),
        size=Quantity.from_int(50_000),
        aggressor_side=AggressorSide.BUYER,
        trade_id=TradeId("123456"),
        ts_event=0,
        ts_init=0,
    )

    assert tick1 == tick2


def test_trade_tick_pickle_roundtrip(audusd_sim_id):
    tick = TradeTick(
        instrument_id=audusd_sim_id,
        price=Price.from_str("1.00001"),
        size=Quantity.from_int(50_000),
        aggressor_side=AggressorSide.SELLER,
        trade_id=TradeId("789"),
        ts_event=5,
        ts_init=6,
    )

    pickled = pickle.dumps(tick)
    unpickled = pickle.loads(pickled)  # noqa: S301

    assert unpickled == tick


def test_trade_tick_to_dict_and_from_dict_roundtrip(audusd_sim_id):
    tick = TradeTick(
        instrument_id=audusd_sim_id,
        price=Price.from_str("1.00001"),
        size=Quantity.from_int(50_000),
        aggressor_side=AggressorSide.BUYER,
        trade_id=TradeId("TRADE-1"),
        ts_event=100,
        ts_init=200,
    )

    d = tick.to_dict()
    restored = TradeTick.from_dict(d)

    assert restored.instrument_id == tick.instrument_id
    assert restored.price == tick.price
    assert restored.size == tick.size
    assert restored.aggressor_side == tick.aggressor_side
    assert restored.trade_id == tick.trade_id
    assert restored.ts_event == tick.ts_event
    assert restored.ts_init == tick.ts_init
