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

import pytest

from nautilus_trader.model import ClientOrderId
from nautilus_trader.model import OrderSide
from nautilus_trader.model import OrderStatus
from nautilus_trader.model import OrderType
from nautilus_trader.model import OwnBookOrder
from nautilus_trader.model import OwnOrderBook
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import TimeInForce
from nautilus_trader.model import TraderId


def _make_own_order(
    side=OrderSide.BUY,
    price="1.00000",
    size=100_000,
    client_order_id="O-001",
):
    return OwnBookOrder(
        trader_id=TraderId("TRADER-001"),
        client_order_id=ClientOrderId(client_order_id),
        side=side,
        price=Price.from_str(price),
        size=Quantity.from_int(size),
        order_type=OrderType.LIMIT,
        time_in_force=TimeInForce.GTC,
        status=OrderStatus.ACCEPTED,
        ts_last=0,
        ts_accepted=0,
        ts_submitted=0,
        ts_init=0,
    )


@pytest.fixture
def book(audusd_id):
    return OwnOrderBook(instrument_id=audusd_id)


def test_own_order_book_construction(book, audusd_id):
    assert book.instrument_id == audusd_id
    assert book.update_count == 0


def test_own_book_order_construction():
    order = _make_own_order()

    assert order.client_order_id == ClientOrderId("O-001")
    assert order.side == OrderSide.BUY
    assert order.price == Price.from_str("1.00000")
    assert order.size == Quantity.from_int(100_000)


def test_own_book_order_hash():
    order = _make_own_order()

    assert isinstance(hash(order), int)


def test_add_and_query(book):
    bid = _make_own_order(side=OrderSide.BUY, price="1.00000", client_order_id="O-001")
    ask = _make_own_order(side=OrderSide.SELL, price="1.00010", client_order_id="O-002")

    book.add(bid)
    book.add(ask)

    assert book.is_order_in_book(ClientOrderId("O-001"))
    assert book.is_order_in_book(ClientOrderId("O-002"))
    assert not book.is_order_in_book(ClientOrderId("O-999"))
    assert len(book.orders_to_list()) == 2
    assert len(book.bids_to_list()) == 1
    assert len(book.asks_to_list()) == 1


def test_bid_and_ask_client_order_ids(book):
    bid = _make_own_order(side=OrderSide.BUY, client_order_id="O-001")
    ask = _make_own_order(side=OrderSide.SELL, price="1.00010", client_order_id="O-002")

    book.add(bid)
    book.add(ask)

    assert book.bid_client_order_ids() == [ClientOrderId("O-001")]
    assert book.ask_client_order_ids() == [ClientOrderId("O-002")]


def test_delete(book):
    order = _make_own_order()
    book.add(order)

    assert book.is_order_in_book(ClientOrderId("O-001"))

    book.delete(order)

    assert not book.is_order_in_book(ClientOrderId("O-001"))
    assert len(book.orders_to_list()) == 0


def test_clear(book):
    book.add(_make_own_order(client_order_id="O-001"))
    book.add(_make_own_order(side=OrderSide.SELL, price="1.00010", client_order_id="O-002"))

    book.clear()

    assert len(book.orders_to_list()) == 0


def test_reset(book):
    book.add(_make_own_order())

    book.reset()

    assert len(book.orders_to_list()) == 0
