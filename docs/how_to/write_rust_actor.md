# Write a Rust actor

An actor receives market data, custom data/signals, and system events but does not manage orders.
This guide walks through building a `SpreadMonitor` that subscribes to quotes
and logs the bid-ask spread.

For background on actors, traits, and handler dispatch, see the
[Actors](../concepts/actors.md) and [Rust](../concepts/rust.md) concept guides.

## Define the struct

An actor owns a `DataActorCore` and any state it needs. The core provides
subscription methods, cache access, and clock access through `Deref`.

```rust
use std::ops::{Deref, DerefMut};

use nautilus_common::actor::{DataActor, DataActorConfig, DataActorCore};
use nautilus_model::{data::QuoteTick, identifiers::{ActorId, InstrumentId}};

pub struct SpreadMonitor {
    core: DataActorCore,
    instrument_id: InstrumentId,
}
```

## Implement the constructor

Create a `DataActorConfig` with an actor ID, then pass it to `DataActorCore::new`.
The config fields use `Option` with defaults, so `..Default::default()` covers
everything except the actor ID.

```rust
impl SpreadMonitor {
    pub fn new(instrument_id: InstrumentId) -> Self {
        let config = DataActorConfig {
            actor_id: Some(ActorId::from("SPREAD_MON-001")),
            ..Default::default()
        };
        Self {
            core: DataActorCore::new(config),
            instrument_id,
        }
    }
}
```

## Implement Deref, DerefMut, and Debug

These three impls are required boilerplate for every actor:

- `Deref<Target = DataActorCore>` gives your struct direct access to
  subscription methods, cache, and clock.
- `DerefMut` allows mutable access to the core.
- `Debug` is a trait bound on `DataActor` (required by the blanket
  `Component` impl).

```rust
impl Deref for SpreadMonitor {
    type Target = DataActorCore;
    fn deref(&self) -> &Self::Target { &self.core }
}

impl DerefMut for SpreadMonitor {
    fn deref_mut(&mut self) -> &mut Self::Target { &mut self.core }
}

impl std::fmt::Debug for SpreadMonitor {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SpreadMonitor").finish()
    }
}
```

## Implement the DataActor trait

Override handler methods to receive data. All handlers have default no-op
implementations, so you only override what you need. Each handler returns
`anyhow::Result<()>`.

```rust
impl DataActor for SpreadMonitor {
    fn on_start(&mut self) -> anyhow::Result<()> {
        self.subscribe_quotes(self.instrument_id, None, None);
        Ok(())
    }

    fn on_quote(&mut self, quote: &QuoteTick) -> anyhow::Result<()> {
        let spread = quote.ask_price.as_f64() - quote.bid_price.as_f64();
        log::info!("Spread: {spread:.5}");
        Ok(())
    }
}
```

`subscribe_quotes` is available directly on `self` because of the `Deref` to
`DataActorCore`. See the
[handler table](../concepts/rust.md#handler-methods) for all available
handlers.

## Register the actor

With a `BacktestEngine`:

```rust
let actor = SpreadMonitor::new(instrument_id);
engine.add_actor(actor)?;
```

With a `LiveNode`:

```rust
let actor = SpreadMonitor::new(instrument_id);
node.add_actor(actor)?;
```

## Full example

See
[`BookImbalanceActor`](https://github.com/nautechsystems/nautilus_trader/tree/develop/crates/trading/src/examples/actors/imbalance)
for a more complete actor that tracks per-instrument state and prints a
summary on stop.
