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

from nautilus_trader.core import UUID4
from nautilus_trader.model import ClientOrderId
from nautilus_trader.model import ContingencyType
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import LimitOrder
from nautilus_trader.model import MarketOrder
from nautilus_trader.model import OrderSide
from nautilus_trader.model import OrderStatus
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import StrategyId
from nautilus_trader.model import TimeInForce
from nautilus_trader.model import TraderId


def test_market_order_construction():
    order = MarketOrder(
        trader_id=TraderId("TRADER-001"),
        strategy_id=StrategyId("S-001"),
        instrument_id=InstrumentId.from_str("AUD/USD.SIM"),
        client_order_id=ClientOrderId("O-001"),
        order_side=OrderSide.BUY,
        quantity=Quantity.from_int(100_000),
        init_id=UUID4(),
        ts_init=0,
        time_in_force=TimeInForce.GTC,
        reduce_only=False,
        quote_quantity=False,
        contingency_type=ContingencyType.NO_CONTINGENCY,
    )

    assert order.trader_id == TraderId("TRADER-001")
    assert order.strategy_id == StrategyId("S-001")
    assert order.instrument_id == InstrumentId.from_str("AUD/USD.SIM")
    assert order.client_order_id == ClientOrderId("O-001")
    assert order.side == OrderSide.BUY
    assert order.quantity == Quantity.from_int(100_000)
    assert order.time_in_force == TimeInForce.GTC
    assert order.status == OrderStatus.INITIALIZED
    assert order.is_reduce_only is False
    assert order.is_quote_quantity is False


def test_market_order_opposite_side():
    assert MarketOrder.opposite_side(OrderSide.BUY) == OrderSide.SELL
    assert MarketOrder.opposite_side(OrderSide.SELL) == OrderSide.BUY


def test_limit_order_construction():
    order = LimitOrder(
        trader_id=TraderId("TRADER-001"),
        strategy_id=StrategyId("S-001"),
        instrument_id=InstrumentId.from_str("AUD/USD.SIM"),
        client_order_id=ClientOrderId("O-002"),
        order_side=OrderSide.SELL,
        quantity=Quantity.from_int(50_000),
        price=Price.from_str("1.00010"),
        time_in_force=TimeInForce.GTC,
        post_only=False,
        reduce_only=False,
        quote_quantity=False,
        init_id=UUID4(),
        ts_init=0,
        expire_time=0,
        display_qty=None,
        contingency_type=ContingencyType.NO_CONTINGENCY,
    )

    assert order.trader_id == TraderId("TRADER-001")
    assert order.strategy_id == StrategyId("S-001")
    assert order.instrument_id == InstrumentId.from_str("AUD/USD.SIM")
    assert order.client_order_id == ClientOrderId("O-002")
    assert order.side == OrderSide.SELL
    assert order.quantity == Quantity.from_int(50_000)
    assert order.price == Price.from_str("1.00010")
    assert order.status == OrderStatus.INITIALIZED
