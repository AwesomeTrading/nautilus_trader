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

import pytest

from nautilus_trader.common import ComponentState
from nautilus_trader.common import CustomData
from nautilus_trader.common import DataActor
from nautilus_trader.common import Signal
from nautilus_trader.model import ActorId
from nautilus_trader.model import AggressorSide
from nautilus_trader.model import Bar
from nautilus_trader.model import BarType
from nautilus_trader.model import Blockchain
from nautilus_trader.model import BookAction
from nautilus_trader.model import BookOrder
from nautilus_trader.model import BookType
from nautilus_trader.model import Chain
from nautilus_trader.model import ClientId
from nautilus_trader.model import DataType
from nautilus_trader.model import Dex
from nautilus_trader.model import FundingRateUpdate
from nautilus_trader.model import IndexPriceUpdate
from nautilus_trader.model import InstrumentClose
from nautilus_trader.model import InstrumentCloseType
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import InstrumentStatus
from nautilus_trader.model import MarketStatusAction
from nautilus_trader.model import MarkPriceUpdate
from nautilus_trader.model import OptionChainSlice
from nautilus_trader.model import OptionGreeks
from nautilus_trader.model import OptionSeriesId
from nautilus_trader.model import OrderBook
from nautilus_trader.model import OrderBookDelta
from nautilus_trader.model import OrderBookDeltas
from nautilus_trader.model import OrderSide
from nautilus_trader.model import Pool
from nautilus_trader.model import PoolFeeCollect
from nautilus_trader.model import PoolFlash
from nautilus_trader.model import PoolLiquidityUpdate
from nautilus_trader.model import PoolLiquidityUpdateType
from nautilus_trader.model import PoolSwap
from nautilus_trader.model import Price
from nautilus_trader.model import Quantity
from nautilus_trader.model import QuoteTick
from nautilus_trader.model import Token
from nautilus_trader.model import TradeId
from nautilus_trader.model import TradeTick
from nautilus_trader.model import Venue
from tests.providers import TestInstrumentProvider
from tests.unit.common.actor import TestActor
from tests.unit.common.actor import TestActorConfig


LIFECYCLE_METHODS = [
    "start",
    "stop",
    "resume",
    "reset",
    "dispose",
    "degrade",
    "fault",
]

HOOK_METHODS = [
    "on_start",
    "on_stop",
    "on_resume",
    "on_reset",
    "on_dispose",
    "on_degrade",
    "on_fault",
]

TYPED_CALLBACKS = [
    ("on_data", "custom_data"),
    ("on_signal", "signal"),
    ("on_instrument", "instrument"),
    ("on_quote", "quote"),
    ("on_trade", "trade"),
    ("on_bar", "bar"),
    ("on_book_deltas", "book_deltas"),
    ("on_book", "book"),
    ("on_mark_price", "mark_price"),
    ("on_index_price", "index_price"),
    ("on_funding_rate", "funding_rate"),
    ("on_instrument_status", "instrument_status"),
    ("on_instrument_close", "instrument_close"),
    ("on_option_greeks", "option_greeks"),
    ("on_option_chain", "option_chain"),
    ("on_pool", "pool"),
    ("on_pool_swap", "pool_swap"),
    ("on_pool_liquidity_update", "pool_liquidity_update"),
    ("on_pool_fee_collect", "pool_fee_collect"),
    ("on_pool_flash", "pool_flash"),
]

HISTORICAL_CALLBACKS = [
    ("on_historical_data", "historical_data"),
    ("on_historical_quotes", "historical_quotes"),
    ("on_historical_trades", "historical_trades"),
    ("on_historical_bars", "historical_bars"),
    ("on_historical_mark_prices", "historical_mark_prices"),
    ("on_historical_index_prices", "historical_index_prices"),
]

REGISTRATION_REQUIRED_METHODS = [
    "shutdown_system",
    "subscribe_data",
    "request_data",
    "unsubscribe_data",
    "subscribe_instruments",
    "subscribe_instrument",
    "subscribe_book_deltas",
    "subscribe_book_at_interval",
    "subscribe_quotes",
    "subscribe_trades",
    "subscribe_bars",
    "subscribe_mark_prices",
    "subscribe_index_prices",
    "subscribe_funding_rates",
    "subscribe_instrument_status",
    "subscribe_instrument_close",
    "subscribe_order_fills",
    "subscribe_order_cancels",
    "subscribe_blocks",
    "subscribe_pool",
    "subscribe_pool_swaps",
    "subscribe_pool_liquidity_updates",
    "subscribe_pool_fee_collects",
    "subscribe_pool_flash_events",
    "request_instrument",
    "request_instruments",
    "request_book_snapshot",
    "request_quotes",
    "request_trades",
    "request_bars",
    "unsubscribe_instruments",
    "unsubscribe_instrument",
    "unsubscribe_book_deltas",
    "unsubscribe_book_at_interval",
    "unsubscribe_quotes",
    "unsubscribe_trades",
    "unsubscribe_bars",
    "unsubscribe_mark_prices",
    "unsubscribe_index_prices",
    "unsubscribe_instrument_status",
    "unsubscribe_instrument_close",
    "unsubscribe_order_fills",
    "unsubscribe_order_cancels",
    "unsubscribe_blocks",
    "unsubscribe_pool",
    "unsubscribe_pool_swaps",
    "unsubscribe_pool_liquidity_updates",
    "unsubscribe_pool_fee_collects",
    "unsubscribe_pool_flash_events",
]


def test_data_actor_pre_registration_surface(actor):
    assert isinstance(actor, DataActor)
    assert actor.log.name == "ACTOR-001"
    assert actor.actor_id == ActorId("ACTOR-001")
    assert actor.trader_id is None
    assert actor.state() == ComponentState.PRE_INITIALIZED
    assert actor.is_ready() is False
    assert actor.is_running() is False
    assert actor.is_stopped() is False
    assert actor.is_degraded() is False
    assert actor.is_faulted() is False
    assert actor.is_disposed() is False

    with pytest.raises(RuntimeError, match="registered with a trader"):
        _ = actor.clock

    with pytest.raises(RuntimeError, match="registered with a trader"):
        _ = actor.cache


@pytest.mark.parametrize("method_name", LIFECYCLE_METHODS)
def test_data_actor_lifecycle_methods_reject_pre_initialized_state(actor, method_name):
    with pytest.raises(RuntimeError, match="Invalid state trigger PRE_INITIALIZED"):
        getattr(actor, method_name)()


@pytest.mark.parametrize("method_name", HOOK_METHODS)
def test_data_actor_lifecycle_hooks_are_callable(actor, method_name):
    assert getattr(actor, method_name)() is None


@pytest.mark.parametrize(("method_name", "sample_name"), TYPED_CALLBACKS)
def test_data_actor_typed_callbacks_accept_runtime_objects(
    actor,
    sample_objects,
    method_name,
    sample_name,
):
    assert getattr(actor, method_name)(sample_objects[sample_name]) is None


@pytest.mark.parametrize(("method_name", "sample_name"), HISTORICAL_CALLBACKS)
def test_data_actor_historical_callbacks_accept_runtime_objects(
    actor,
    sample_objects,
    method_name,
    sample_name,
):
    assert getattr(actor, method_name)(sample_objects[sample_name]) is None


@pytest.mark.parametrize(
    ("method_name", "pattern"),
    [
        ("on_time_event", "TimeEvent"),
        ("on_block", "Block"),
    ],
)
def test_data_actor_runtime_only_callbacks_reject_unavailable_public_types(
    actor,
    method_name,
    pattern,
):
    with pytest.raises(TypeError, match=pattern):
        getattr(actor, method_name)(object())


@pytest.mark.parametrize("method_name", REGISTRATION_REQUIRED_METHODS)
def test_data_actor_runtime_methods_require_registration(actor, method_name):
    with pytest.raises(BaseException, match="registered"):
        getattr(actor, method_name)(**_registration_kwargs(method_name))


@pytest.fixture
def actor():
    config = TestActorConfig(
        actor_id=ActorId("ACTOR-001"),
        log_events=False,
        log_commands=False,
    )
    return TestActor(config)


@pytest.fixture
def sample_objects():
    instrument = TestInstrumentProvider.audusd_sim()
    quote = _make_quote(instrument.id)
    trade = _make_trade(instrument.id)
    bar = _make_bar(instrument.id)
    book_deltas = _make_book_deltas(instrument.id)
    option_greeks = _make_option_greeks()
    option_chain = _make_option_chain()
    pool = _make_pool()

    return {
        "custom_data": CustomData(DataType("X"), [1, 2], 3, 4),
        "signal": Signal("sig", "value", 1, 2),
        "instrument": instrument,
        "quote": quote,
        "trade": trade,
        "bar": bar,
        "book_deltas": book_deltas,
        "book": OrderBook(instrument.id, BookType.L2_MBP),
        "mark_price": MarkPriceUpdate(instrument.id, Price.from_str("1.00000"), 1, 2),
        "index_price": IndexPriceUpdate(instrument.id, Price.from_str("1.00000"), 1, 2),
        "funding_rate": FundingRateUpdate(instrument.id, Decimal("0.0001"), 1, 2, interval=480),
        "instrument_status": InstrumentStatus(instrument.id, MarketStatusAction.TRADING, 1, 2),
        "instrument_close": InstrumentClose(
            instrument.id,
            Price.from_str("1.00000"),
            InstrumentCloseType.END_OF_SESSION,
            1,
            2,
        ),
        "option_greeks": option_greeks,
        "option_chain": option_chain,
        "pool": pool,
        "pool_swap": _make_pool_swap(pool),
        "pool_liquidity_update": _make_pool_liquidity_update(pool),
        "pool_fee_collect": _make_pool_fee_collect(pool),
        "pool_flash": _make_pool_flash(pool),
        "historical_data": [CustomData(DataType("X"), [1, 2], 3, 4)],
        "historical_quotes": [quote],
        "historical_trades": [trade],
        "historical_bars": [bar],
        "historical_mark_prices": [MarkPriceUpdate(instrument.id, Price.from_str("1.00000"), 1, 2)],
        "historical_index_prices": [
            IndexPriceUpdate(instrument.id, Price.from_str("1.00000"), 1, 2),
        ],
    }


def _registration_kwargs(method_name):
    context = _registration_context()

    builders = {
        "shutdown_system": _shutdown_system_kwargs,
        "subscribe_data": _data_subscription_kwargs,
        "request_data": _data_request_kwargs,
        "unsubscribe_data": _data_subscription_kwargs,
        "subscribe_instruments": _venue_subscription_kwargs,
        "unsubscribe_instruments": _venue_subscription_kwargs,
        "request_instruments": _venue_request_kwargs,
        "subscribe_instrument": _instrument_subscription_kwargs,
        "unsubscribe_instrument": _instrument_subscription_kwargs,
        "subscribe_quotes": _instrument_subscription_kwargs,
        "unsubscribe_quotes": _instrument_subscription_kwargs,
        "subscribe_trades": _instrument_subscription_kwargs,
        "unsubscribe_trades": _instrument_subscription_kwargs,
        "subscribe_mark_prices": _instrument_subscription_kwargs,
        "unsubscribe_mark_prices": _instrument_subscription_kwargs,
        "subscribe_index_prices": _instrument_subscription_kwargs,
        "unsubscribe_index_prices": _instrument_subscription_kwargs,
        "subscribe_funding_rates": _instrument_subscription_kwargs,
        "subscribe_instrument_status": _instrument_subscription_kwargs,
        "unsubscribe_instrument_status": _instrument_subscription_kwargs,
        "subscribe_instrument_close": _instrument_subscription_kwargs,
        "unsubscribe_instrument_close": _instrument_subscription_kwargs,
        "subscribe_pool": _instrument_subscription_kwargs,
        "unsubscribe_pool": _instrument_subscription_kwargs,
        "subscribe_pool_swaps": _instrument_subscription_kwargs,
        "unsubscribe_pool_swaps": _instrument_subscription_kwargs,
        "subscribe_pool_liquidity_updates": _instrument_subscription_kwargs,
        "unsubscribe_pool_liquidity_updates": _instrument_subscription_kwargs,
        "subscribe_pool_fee_collects": _instrument_subscription_kwargs,
        "unsubscribe_pool_fee_collects": _instrument_subscription_kwargs,
        "subscribe_pool_flash_events": _instrument_subscription_kwargs,
        "unsubscribe_pool_flash_events": _instrument_subscription_kwargs,
        "subscribe_order_fills": _order_subscription_kwargs,
        "unsubscribe_order_fills": _order_subscription_kwargs,
        "subscribe_order_cancels": _order_subscription_kwargs,
        "unsubscribe_order_cancels": _order_subscription_kwargs,
        "subscribe_book_deltas": _book_deltas_subscription_kwargs,
        "unsubscribe_book_deltas": _instrument_subscription_kwargs,
        "subscribe_book_at_interval": _book_interval_subscription_kwargs,
        "unsubscribe_book_at_interval": _book_interval_unsubscribe_kwargs,
        "subscribe_bars": _bar_subscription_kwargs,
        "unsubscribe_bars": _bar_subscription_kwargs,
        "request_instrument": _instrument_request_kwargs,
        "request_book_snapshot": _book_snapshot_request_kwargs,
        "request_quotes": _instrument_history_request_kwargs,
        "request_trades": _instrument_history_request_kwargs,
        "request_bars": _bar_request_kwargs,
        "subscribe_blocks": _block_subscription_kwargs,
        "unsubscribe_blocks": _block_subscription_kwargs,
    }

    try:
        return builders[method_name](context)
    except KeyError as exc:
        raise ValueError(f"Unhandled method: {method_name}") from exc


def _registration_context():
    instrument_id = TestInstrumentProvider.audusd_sim().id
    return {
        "instrument_id": instrument_id,
        "client_id": ClientId("CLIENT-001"),
        "bar_type": BarType.from_str(f"{instrument_id}-1-MINUTE-LAST-EXTERNAL"),
        "params": {"key": "value"},
    }


def _shutdown_system_kwargs(_context):
    return {"reason": "test"}


def _data_subscription_kwargs(context):
    return {
        "data_type": DataType("X"),
        "client_id": context["client_id"],
        "params": context["params"],
    }


def _data_request_kwargs(context):
    return _data_subscription_kwargs(context) | {"start": 1, "end": 2, "limit": 3}


def _venue_subscription_kwargs(context):
    return {
        "venue": Venue("SIM"),
        "client_id": context["client_id"],
        "params": context["params"],
    }


def _venue_request_kwargs(context):
    return _venue_subscription_kwargs(context) | {"start": 1, "end": 2}


def _instrument_subscription_kwargs(context):
    return {
        "instrument_id": context["instrument_id"],
        "client_id": context["client_id"],
        "params": context["params"],
    }


def _order_subscription_kwargs(context):
    return {"instrument_id": context["instrument_id"]}


def _book_deltas_subscription_kwargs(context):
    return _instrument_subscription_kwargs(context) | {
        "book_type": BookType.L2_MBP,
        "depth": 5,
        "managed": True,
    }


def _book_interval_subscription_kwargs(context):
    return _instrument_subscription_kwargs(context) | {
        "book_type": BookType.L2_MBP,
        "interval_ms": 1_000,
        "depth": 5,
    }


def _book_interval_unsubscribe_kwargs(context):
    return _instrument_subscription_kwargs(context) | {"interval_ms": 1_000}


def _bar_subscription_kwargs(context):
    return {
        "bar_type": context["bar_type"],
        "client_id": context["client_id"],
        "params": context["params"],
    }


def _instrument_request_kwargs(context):
    return _instrument_subscription_kwargs(context) | {"start": 1, "end": 2}


def _book_snapshot_request_kwargs(context):
    return _instrument_subscription_kwargs(context) | {"depth": 5}


def _instrument_history_request_kwargs(context):
    return _instrument_subscription_kwargs(context) | {"start": 1, "end": 2, "limit": 3}


def _bar_request_kwargs(context):
    return _bar_subscription_kwargs(context) | {"start": 1, "end": 2, "limit": 3}


def _block_subscription_kwargs(context):
    return {
        "chain": Blockchain.BASE,
        "client_id": context["client_id"],
        "params": context["params"],
    }


def _make_quote(instrument_id):
    return QuoteTick(
        instrument_id,
        Price.from_str("1.00000"),
        Price.from_str("1.00001"),
        Quantity.from_int(1),
        Quantity.from_int(2),
        1,
        2,
    )


def _make_trade(instrument_id):
    return TradeTick(
        instrument_id,
        Price.from_str("1.00000"),
        Quantity.from_int(10),
        AggressorSide.BUYER,
        TradeId("T-001"),
        1,
        2,
    )


def _make_bar(instrument_id):
    bar_type = BarType.from_str(f"{instrument_id}-1-MINUTE-LAST-EXTERNAL")
    return Bar(
        bar_type,
        Price.from_str("1.00000"),
        Price.from_str("1.10000"),
        Price.from_str("0.90000"),
        Price.from_str("1.05000"),
        Quantity.from_int(10),
        1,
        2,
    )


def _make_book_deltas(instrument_id):
    bid = BookOrder(OrderSide.BUY, Price.from_str("1.00000"), Quantity.from_int(1), 1)
    ask = BookOrder(OrderSide.SELL, Price.from_str("1.10000"), Quantity.from_int(2), 2)
    delta1 = OrderBookDelta(instrument_id, BookAction.ADD, bid, 0, 1, 1, 2)
    delta2 = OrderBookDelta(instrument_id, BookAction.ADD, ask, 0, 2, 1, 2)
    return OrderBookDeltas(instrument_id, [delta1, delta2])


def _make_option_greeks():
    instrument_id = InstrumentId.from_str("BTC-20240329-50000-C.DERIBIT")
    return OptionGreeks(
        instrument_id,
        0.5,
        0.1,
        0.2,
        -0.3,
        0.05,
        0.6,
        0.55,
        0.65,
        50_000.0,
        42.0,
        3,
        4,
    )


def _make_option_chain():
    series_id = OptionSeriesId.from_expiry("DERIBIT", "BTC", "USD", "2024-03-29")
    return OptionChainSlice(series_id, Price.from_str("50000.0"), 5, 6)


def _make_pool():
    chain = Chain(Blockchain.BASE, 8453)
    dex = _make_dex(chain)
    token0 = _make_token0(chain)
    token1 = _make_token1(chain)
    return Pool(
        chain=chain,
        dex=dex,
        address="0x0000000000000000000000000000000000000003",
        pool_identifier="0x0000000000000000000000000000000000000003",
        creation_block=1,
        token0=token0,
        token1=token1,
        fee=500,
        tick_spacing=10,
        ts_init=2,
    )


def _make_pool_swap(pool):
    return PoolSwap(
        chain=pool.chain,
        dex=pool.dex,
        instrument_id=pool.instrument_id,
        pool_identifier=pool.address,
        block=1,
        transaction_hash="0x3333333333333333333333333333333333333333333333333333333333333333",
        transaction_index=0,
        log_index=1,
        timestamp=10,
        sender="0x0000000000000000000000000000000000000004",
        receiver="0x0000000000000000000000000000000000000005",
        amount0="1",
        amount1="-2",
        sqrt_price_x96="79228162514264337593543950336",
        liquidity=100,
        tick=1,
    )


def _make_pool_liquidity_update(pool):
    return PoolLiquidityUpdate(
        chain=pool.chain,
        dex=pool.dex,
        pool_identifier=pool.address,
        instrument_id=pool.instrument_id,
        kind=PoolLiquidityUpdateType.MINT,
        block=1,
        transaction_hash="0x4444444444444444444444444444444444444444444444444444444444444444",
        transaction_index=0,
        log_index=1,
        sender=None,
        owner="0x0000000000000000000000000000000000000004",
        position_liquidity="10",
        amount0="1",
        amount1="2",
        tick_lower=-10,
        tick_upper=10,
        timestamp=10,
    )


def _make_pool_fee_collect(pool):
    return PoolFeeCollect(
        chain=pool.chain,
        dex=pool.dex,
        pool_identifier=pool.address,
        instrument_id=pool.instrument_id,
        block=1,
        transaction_hash="0x5555555555555555555555555555555555555555555555555555555555555555",
        transaction_index=0,
        log_index=1,
        owner="0x0000000000000000000000000000000000000004",
        amount0="1",
        amount1="2",
        tick_lower=-10,
        tick_upper=10,
        timestamp=10,
    )


def _make_pool_flash(pool):
    return PoolFlash(
        chain=pool.chain,
        dex=pool.dex,
        pool_identifier=pool.address,
        instrument_id=pool.instrument_id,
        block=1,
        transaction_hash="0x6666666666666666666666666666666666666666666666666666666666666666",
        transaction_index=0,
        log_index=1,
        sender="0x0000000000000000000000000000000000000004",
        recipient="0x0000000000000000000000000000000000000005",
        amount0="1",
        amount1="2",
        paid0="3",
        paid1="4",
        timestamp=10,
    )


def _make_dex(chain):
    return Dex(
        chain=chain,
        name="UniswapV3",
        factory="0x0000000000000000000000000000000000000fac",
        factory_creation_block=1,
        amm_type="CLAMM",
        pool_created_event="PoolCreated",
        swap_event="Swap",
        mint_event="Mint",
        burn_event="Burn",
        collect_event="Collect",
    )


def _make_token0(chain):
    return Token(
        chain=chain,
        address="0x0000000000000000000000000000000000000001",
        name="USD Coin",
        symbol="USDC",
        decimals=6,
    )


def _make_token1(chain):
    return Token(
        chain=chain,
        address="0x0000000000000000000000000000000000000002",
        name="Wrapped Ether",
        symbol="WETH",
        decimals=18,
    )
