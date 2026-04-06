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

from nautilus_trader.common import Cache
from nautilus_trader.common import FifoCache
from nautilus_trader.model import AccountId
from nautilus_trader.model import AggregationSource
from nautilus_trader.model import BarType
from nautilus_trader.model import ClientOrderId
from nautilus_trader.model import Currency
from nautilus_trader.model import ExecAlgorithmId
from nautilus_trader.model import OrderListId
from nautilus_trader.model import OrderSide
from nautilus_trader.model import PositionId
from nautilus_trader.model import PositionSide
from nautilus_trader.model import PriceType
from nautilus_trader.model import StrategyId
from nautilus_trader.model import Venue
from nautilus_trader.model import VenueOrderId
from tests.providers import TestInstrumentProvider


AUDUSD_SIM = TestInstrumentProvider.audusd_sim()
INSTRUMENT_ID = AUDUSD_SIM.id
VENUE = Venue("SIM")
ACCOUNT_ID = AccountId("SIM-001")
STRATEGY_ID = StrategyId("S-001")
CLIENT_ORDER_ID = ClientOrderId("O-001")
VENUE_ORDER_ID = VenueOrderId("VO-001")
EXEC_ALGORITHM_ID = ExecAlgorithmId("ALGO-001")
POSITION_ID = PositionId("P-001")
ORDER_LIST_ID = OrderListId("OL-001")
BAR_TYPE = BarType.from_str(f"{INSTRUMENT_ID}-1-MINUTE-LAST-EXTERNAL")
USD = Currency.from_str("USD")
EUR = Currency.from_str("EUR")
ORDER_SIDE = OrderSide.BUY
POSITION_SIDE = PositionSide.LONG

CACHE_NONE_CASES = [
    ("account", (ACCOUNT_ID,)),
    ("account_for_venue", (VENUE,)),
    ("account_id", (VENUE,)),
    ("bar", (BAR_TYPE, 1)),
    ("bars", (BAR_TYPE,)),
    ("client_id", (CLIENT_ORDER_ID,)),
    ("client_order_id", (VENUE_ORDER_ID,)),
    ("exec_spawn_total_filled_qty", (CLIENT_ORDER_ID, True)),
    ("exec_spawn_total_leaves_qty", (CLIENT_ORDER_ID, True)),
    ("exec_spawn_total_quantity", (CLIENT_ORDER_ID, True)),
    ("funding_rate", (INSTRUMENT_ID,)),
    ("get", ("missing",)),
    ("get_mark_xrate", (USD, EUR)),
    ("get_xrate", (VENUE, USD, EUR, PriceType.MID)),
    ("index_price", (INSTRUMENT_ID,)),
    ("index_prices", (INSTRUMENT_ID,)),
    ("instrument", (INSTRUMENT_ID,)),
    ("mark_price", (INSTRUMENT_ID,)),
    ("mark_prices", (INSTRUMENT_ID,)),
    ("order", (CLIENT_ORDER_ID,)),
    ("order_book", (INSTRUMENT_ID,)),
    ("order_list", (ORDER_LIST_ID,)),
    ("own_order_book", (INSTRUMENT_ID,)),
    ("pool", (INSTRUMENT_ID,)),
    ("pool_profiler", (INSTRUMENT_ID,)),
    ("position", (POSITION_ID,)),
    ("position_for_order", (CLIENT_ORDER_ID,)),
    ("position_id", (CLIENT_ORDER_ID,)),
    ("position_snapshot_bytes", (POSITION_ID,)),
    ("price", (INSTRUMENT_ID, PriceType.MID)),
    ("quote", (INSTRUMENT_ID, 1)),
    ("quotes", (INSTRUMENT_ID,)),
    ("strategy_id_for_order", (CLIENT_ORDER_ID,)),
    ("strategy_id_for_position", (POSITION_ID,)),
    ("synthetic", (INSTRUMENT_ID,)),
    ("trade", (INSTRUMENT_ID, 1)),
    ("trades", (INSTRUMENT_ID,)),
    ("venue_order_id", (CLIENT_ORDER_ID,)),
]

CACHE_LIST_CASES = [
    ("actor_ids", ()),
    ("bar_types", (AggregationSource.EXTERNAL,)),
    ("bar_types", (AggregationSource.EXTERNAL, INSTRUMENT_ID, PriceType.MID)),
    ("client_order_ids", ()),
    ("client_order_ids", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("client_order_ids_closed", ()),
    ("client_order_ids_closed", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("client_order_ids_emulated", ()),
    ("client_order_ids_emulated", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("client_order_ids_inflight", ()),
    ("client_order_ids_inflight", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("client_order_ids_open", ()),
    ("client_order_ids_open", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("exec_algorithm_ids", ()),
    ("instrument_ids", ()),
    ("instrument_ids", (VENUE,)),
    ("instruments", ()),
    ("instruments", (VENUE,)),
    ("order_lists", ()),
    ("order_lists", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("orders", ()),
    ("orders", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_closed", ()),
    ("orders_closed", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_emulated", ()),
    ("orders_emulated", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_for_exec_algorithm", (EXEC_ALGORITHM_ID,)),
    (
        "orders_for_exec_algorithm",
        (EXEC_ALGORITHM_ID, VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE),
    ),
    ("orders_for_exec_spawn", (CLIENT_ORDER_ID,)),
    ("orders_for_position", (POSITION_ID,)),
    ("orders_inflight", ()),
    ("orders_inflight", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_open", ()),
    ("orders_open", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("position_closed_ids", ()),
    ("position_closed_ids", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("position_ids", ()),
    ("position_ids", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("position_open_ids", ()),
    ("position_open_ids", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID)),
    ("positions", ()),
    ("positions", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, POSITION_SIDE)),
    ("positions_closed", ()),
    ("positions_closed", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, POSITION_SIDE)),
    ("positions_open", ()),
    ("positions_open", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, POSITION_SIDE)),
    ("strategy_ids", ()),
    ("synthetic_ids", ()),
]

CACHE_FALSE_CASES = [
    ("has_bars", (BAR_TYPE,)),
    ("has_order_book", (INSTRUMENT_ID,)),
    ("has_quote_ticks", (INSTRUMENT_ID,)),
    ("has_trade_ticks", (INSTRUMENT_ID,)),
    ("is_order_closed", (CLIENT_ORDER_ID,)),
    ("is_order_emulated", (CLIENT_ORDER_ID,)),
    ("is_order_inflight", (CLIENT_ORDER_ID,)),
    ("is_order_open", (CLIENT_ORDER_ID,)),
    ("is_order_pending_cancel_local", (CLIENT_ORDER_ID,)),
    ("is_position_closed", (POSITION_ID,)),
    ("is_position_open", (POSITION_ID,)),
    ("order_exists", (CLIENT_ORDER_ID,)),
    ("order_list_exists", (ORDER_LIST_ID,)),
    ("position_exists", (POSITION_ID,)),
]

CACHE_ZERO_CASES = [
    ("bar_count", (BAR_TYPE,)),
    ("book_update_count", (INSTRUMENT_ID,)),
    ("orders_closed_count", ()),
    ("orders_closed_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_emulated_count", ()),
    ("orders_emulated_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_inflight_count", ()),
    ("orders_inflight_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_open_count", ()),
    ("orders_open_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("orders_total_count", ()),
    ("orders_total_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, ORDER_SIDE)),
    ("positions_closed_count", ()),
    ("positions_closed_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, POSITION_SIDE)),
    ("positions_open_count", ()),
    ("positions_open_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, POSITION_SIDE)),
    ("positions_total_count", ()),
    ("positions_total_count", (VENUE, INSTRUMENT_ID, STRATEGY_ID, ACCOUNT_ID, POSITION_SIDE)),
    ("quote_count", (INSTRUMENT_ID,)),
    ("trade_count", (INSTRUMENT_ID,)),
]


def test_fifo_cache_lifecycle():
    cache = FifoCache()
    cache.add("a")
    cache.add("b")

    assert cache.capacity == 10000
    assert len(cache) == 2
    assert "a" in cache
    assert "b" in cache

    cache.remove("a")

    assert len(cache) == 1
    assert "a" not in cache
    assert "b" in cache

    cache.clear()

    assert len(cache) == 0


def test_cache_constructor_accepts_default_config():
    assert isinstance(Cache(), Cache)


@pytest.mark.parametrize(("method_name", "args"), CACHE_NONE_CASES)
def test_cache_empty_methods_return_none(method_name, args):
    cache = Cache()

    result = getattr(cache, method_name)(*args)

    assert result is None


@pytest.mark.parametrize(("method_name", "args"), CACHE_LIST_CASES)
def test_cache_empty_methods_return_empty_list(method_name, args):
    cache = Cache()

    result = getattr(cache, method_name)(*args)

    assert result == []


@pytest.mark.parametrize(("method_name", "args"), CACHE_FALSE_CASES)
def test_cache_empty_methods_return_false(method_name, args):
    cache = Cache()

    result = getattr(cache, method_name)(*args)

    assert result is False


@pytest.mark.parametrize(("method_name", "args"), CACHE_ZERO_CASES)
def test_cache_empty_methods_return_zero(method_name, args):
    cache = Cache()

    result = getattr(cache, method_name)(*args)

    assert result == 0


def test_cache_add_get_reset_and_dispose():
    cache = Cache()

    assert cache.get("missing") is None

    cache.add("key", [1, 2, 3])

    assert cache.get("key") == b"\x01\x02\x03"

    cache.reset()

    assert cache.get("key") is None

    cache.dispose()
