# Write a Strategy (Rust)

A strategy extends an actor with order management. This guide walks through
building a minimal strategy that subscribes to quotes and submits market
orders. Read [Write an Actor (Rust)](write_rust_actor.md) first.

For background on strategy concepts and order management, see the
[Strategies](../concepts/strategies.md) and [Rust](../concepts/rust.md)
concept guides.

## Define the struct

A strategy owns a `StrategyCore` instead of a `DataActorCore`. The
`StrategyCore` wraps `DataActorCore` and adds an `OrderFactory`,
`OrderManager`, and portfolio integration.

```rust
use std::ops::{Deref, DerefMut};

use nautilus_common::actor::{DataActor, DataActorCore};
use nautilus_model::{
    data::QuoteTick,
    enums::OrderSide,
    identifiers::{InstrumentId, StrategyId},
    types::Quantity,
};
use nautilus_trading::strategy::{Strategy, StrategyConfig, StrategyCore};

pub struct MyStrategy {
    core: StrategyCore,
    instrument_id: InstrumentId,
    trade_size: Quantity,
}
```

## Implement the constructor

`StrategyConfig` takes a `strategy_id` and an `order_id_tag`. The tag is
appended to all client order IDs from this strategy, preventing collisions
when multiple strategies trade the same instrument.

```rust
impl MyStrategy {
    pub fn new(instrument_id: InstrumentId) -> Self {
        let config = StrategyConfig {
            strategy_id: Some(StrategyId::from("MY_STRAT-001")),
            order_id_tag: Some("001".to_string()),
            ..Default::default()
        };
        Self {
            core: StrategyCore::new(config),
            instrument_id,
            trade_size: Quantity::from("1.0"),
        }
    }
}
```

## Implement Deref, DerefMut, and Debug

The `Deref` target is `DataActorCore`, not `StrategyCore`. This is because
`StrategyCore` itself derefs to `DataActorCore`, and Rust's deref coercion
gives your struct access to subscription methods, cache, and clock.

```rust
impl Deref for MyStrategy {
    type Target = DataActorCore;
    fn deref(&self) -> &Self::Target { &self.core }
}

impl DerefMut for MyStrategy {
    fn deref_mut(&mut self) -> &mut Self::Target { &mut self.core }
}

impl std::fmt::Debug for MyStrategy {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("MyStrategy").finish()
    }
}
```

## Implement the DataActor trait

Data handling works the same as in an actor. Subscribe in `on_start`,
respond in handlers.

```rust
impl DataActor for MyStrategy {
    fn on_start(&mut self) -> anyhow::Result<()> {
        self.subscribe_quotes(self.instrument_id, None, None);
        Ok(())
    }

    fn on_quote(&mut self, quote: &QuoteTick) -> anyhow::Result<()> {
        let order = self.core.order_factory().market(
            self.instrument_id,
            OrderSide::Buy,
            self.trade_size,
            None, None, None, None, None, None, None,
        );
        self.submit_order(order, None, None)?;
        Ok(())
    }
}
```

`self.core.order_factory()` builds order objects. Available methods:
`market`, `limit`, `stop_market`, `stop_limit`, `market_if_touched`,
`limit_if_touched`, and `trailing_stop_market`.

`submit_order` is available on `self` through the `Strategy` trait impl
below.

## Implement the Strategy trait

The `Strategy` trait requires two accessors that return references to the
`StrategyCore`. These connect the order submission methods to your struct.

```rust
impl Strategy for MyStrategy {
    fn core(&self) -> &StrategyCore { &self.core }
    fn core_mut(&mut self) -> &mut StrategyCore { &mut self.core }
}
```

## Order management methods

The `Strategy` trait provides these methods through `StrategyCore`:

| Method                | Action                                    |
|-----------------------|-------------------------------------------|
| `submit_order`        | Submit a new order to the venue.          |
| `submit_order_list`   | Submit a list of contingent orders.       |
| `modify_order`        | Modify price, quantity, or trigger price. |
| `cancel_order`        | Cancel a specific order.                  |
| `cancel_orders`       | Cancel a filtered set of orders.          |
| `cancel_all_orders`   | Cancel all orders for an instrument.      |
| `close_position`      | Close a position with a market order.     |
| `close_all_positions` | Close all open positions.                 |

## Full examples

- [`EmaCross`](https://github.com/nautechsystems/nautilus_trader/tree/develop/crates/trading/src/examples/strategies/ema_cross):
  Dual-EMA crossover with indicator integration.
- [`GridMarketMaker`](https://github.com/nautechsystems/nautilus_trader/tree/develop/crates/trading/src/examples/strategies/grid_mm):
  Grid market making with configurable levels and requoting.
