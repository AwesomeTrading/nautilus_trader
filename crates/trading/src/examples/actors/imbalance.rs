// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
//  https://nautechsystems.io
//
//  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
//  You may not use this file except in compliance with the License.
//  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
// -------------------------------------------------------------------------------------------------

//! Order book imbalance actor.
//!
//! Subscribes to order book deltas for a set of instruments and tracks the
//! cumulative bid/ask quoted volume. For each batch of deltas, sums the
//! resting size at each updated price level per side and computes:
//!
//! `imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)`
//!
//! The result ranges from -1.0 (all volume on the ask side) to +1.0 (all
//! volume on the bid side). This measures which side of the book receives
//! more quoted volume across updates, not the incremental change in volume.
//! In a betting exchange context, bids correspond to "back" orders and asks
//! to "lay" orders.

use std::{
    collections::BTreeMap,
    fmt::Debug,
    ops::{Deref, DerefMut},
};

use ahash::AHashMap;
use nautilus_common::actor::{DataActor, DataActorConfig, DataActorCore};
use nautilus_model::{
    data::OrderBookDeltas,
    enums::{BookType, OrderSide},
    identifiers::{ActorId, InstrumentId},
};

/// Per-instrument imbalance tracking state.
#[derive(Debug)]
pub struct ImbalanceState {
    /// Total number of book delta batches processed.
    pub update_count: u64,
    /// Cumulative bid-side volume across all updates.
    pub bid_volume_total: f64,
    /// Cumulative ask-side volume across all updates.
    pub ask_volume_total: f64,
}

impl ImbalanceState {
    /// Creates a new [`ImbalanceState`] with zero counts.
    #[must_use]
    pub fn new() -> Self {
        Self {
            update_count: 0,
            bid_volume_total: 0.0,
            ask_volume_total: 0.0,
        }
    }

    /// Returns the cumulative quoted volume imbalance, or 0.0 if no volume observed.
    #[must_use]
    pub fn imbalance(&self) -> f64 {
        let total = self.bid_volume_total + self.ask_volume_total;
        if total > 0.0 {
            (self.bid_volume_total - self.ask_volume_total) / total
        } else {
            0.0
        }
    }
}

impl Default for ImbalanceState {
    fn default() -> Self {
        Self::new()
    }
}

/// Actor that tracks bid/ask quoted volume imbalance from order book deltas.
///
/// On start, subscribes to [`OrderBookDeltas`] for each configured instrument.
/// On each update, sums the resting size at each updated level per side and
/// accumulates running totals. Logs the cumulative imbalance at a configurable
/// interval. On stop, prints a per-instrument summary.
pub struct BookImbalanceActor {
    core: DataActorCore,
    instrument_ids: Vec<InstrumentId>,
    log_interval: u64,
    states: AHashMap<InstrumentId, ImbalanceState>,
}

impl BookImbalanceActor {
    /// Creates a new [`BookImbalanceActor`].
    ///
    /// `actor_id` sets the actor identifier. Pass `None` for the default
    /// `"BOOK_IMBALANCE-001"`.
    ///
    /// `log_interval` controls how often (in update count) a progress line
    /// is printed. Set to 0 to disable periodic logging.
    #[must_use]
    pub fn new(
        instrument_ids: Vec<InstrumentId>,
        log_interval: u64,
        actor_id: Option<ActorId>,
    ) -> Self {
        let config = DataActorConfig {
            actor_id: Some(actor_id.unwrap_or(ActorId::from("BOOK_IMBALANCE-001"))),
            ..Default::default()
        };
        Self {
            core: DataActorCore::new(config),
            instrument_ids,
            log_interval,
            states: AHashMap::new(),
        }
    }

    /// Returns the per-instrument imbalance states.
    #[must_use]
    pub fn states(&self) -> &AHashMap<InstrumentId, ImbalanceState> {
        &self.states
    }

    /// Prints a summary of all tracked instruments to stdout.
    pub fn print_summary(&self) {
        println!("\n--- Book imbalance summary ---");
        let sorted: BTreeMap<String, &ImbalanceState> = self
            .states
            .iter()
            .map(|(id, state)| (id.to_string(), state))
            .collect();

        for (id, state) in &sorted {
            println!(
                "  {id}  updates: {}  bid_vol: {:.2}  ask_vol: {:.2}  imbalance: {:.4}",
                state.update_count,
                state.bid_volume_total,
                state.ask_volume_total,
                state.imbalance(),
            );
        }
    }
}

impl Deref for BookImbalanceActor {
    type Target = DataActorCore;
    fn deref(&self) -> &Self::Target {
        &self.core
    }
}

impl DerefMut for BookImbalanceActor {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.core
    }
}

impl Debug for BookImbalanceActor {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct(stringify!(BookImbalanceActor))
            .field("instrument_ids", &self.instrument_ids)
            .field("log_interval", &self.log_interval)
            .finish()
    }
}

impl DataActor for BookImbalanceActor {
    fn on_start(&mut self) -> anyhow::Result<()> {
        let ids = self.instrument_ids.clone();
        for instrument_id in ids {
            self.subscribe_book_deltas(
                instrument_id,
                BookType::L2_MBP,
                None,  // depth
                None,  // client_id
                false, // managed
                None,  // params
            );
        }
        Ok(())
    }

    fn on_stop(&mut self) -> anyhow::Result<()> {
        self.print_summary();
        Ok(())
    }

    fn on_book_deltas(&mut self, deltas: &OrderBookDeltas) -> anyhow::Result<()> {
        let mut bid_volume = 0.0;
        let mut ask_volume = 0.0;

        for delta in &deltas.deltas {
            let size = delta.order.size.as_f64();
            match delta.order.side {
                OrderSide::Buy => bid_volume += size,
                OrderSide::Sell => ask_volume += size,
                _ => {}
            }
        }

        let state = self.states.entry(deltas.instrument_id).or_default();

        state.update_count += 1;
        state.bid_volume_total += bid_volume;
        state.ask_volume_total += ask_volume;

        if self.log_interval > 0 && state.update_count.is_multiple_of(self.log_interval) {
            println!(
                "[{}] update #{}: batch bid={:.2} ask={:.2}  cumulative imbalance={:.4}",
                deltas.instrument_id,
                state.update_count,
                bid_volume,
                ask_volume,
                state.imbalance(),
            );
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use nautilus_core::UnixNanos;
    use nautilus_model::{
        data::{BookOrder, OrderBookDelta, OrderBookDeltas},
        enums::{BookAction, OrderSide},
        identifiers::InstrumentId,
        types::{Price, Quantity},
    };
    use rstest::rstest;

    use super::*;

    fn make_delta(
        instrument_id: InstrumentId,
        side: OrderSide,
        price: &str,
        size: &str,
        ts: u64,
    ) -> OrderBookDelta {
        let order = BookOrder::new(side, Price::from(price), Quantity::from(size), 1);
        OrderBookDelta::new(
            instrument_id,
            BookAction::Add,
            order,
            0,
            0,
            UnixNanos::from(ts),
            UnixNanos::from(ts),
        )
    }

    fn make_deltas(instrument_id: InstrumentId, deltas: Vec<OrderBookDelta>) -> OrderBookDeltas {
        OrderBookDeltas::new(instrument_id, deltas)
    }

    fn instrument_a() -> InstrumentId {
        InstrumentId::from("1.123-100.BETFAIR")
    }

    fn instrument_b() -> InstrumentId {
        InstrumentId::from("1.123-200.BETFAIR")
    }

    #[rstest]
    fn test_new_actor_starts_with_empty_states() {
        let actor = BookImbalanceActor::new(vec![instrument_a()], 0, None);

        assert!(actor.states().is_empty());
        assert_eq!(actor.actor_id, ActorId::from("BOOK_IMBALANCE-001"));
    }

    #[rstest]
    fn test_imbalance_zero_when_no_volume() {
        let state = ImbalanceState::new();
        assert_eq!(state.imbalance(), 0.0);
    }

    #[rstest]
    fn test_imbalance_positive_when_bid_dominated() {
        let mut state = ImbalanceState::new();
        state.bid_volume_total = 100.0;
        state.ask_volume_total = 20.0;

        let expected = (100.0 - 20.0) / (100.0 + 20.0);
        assert!((state.imbalance() - expected).abs() < 1e-10);
        assert!(state.imbalance() > 0.0);
    }

    #[rstest]
    fn test_imbalance_negative_when_ask_dominated() {
        let mut state = ImbalanceState::new();
        state.bid_volume_total = 30.0;
        state.ask_volume_total = 70.0;

        let expected = (30.0 - 70.0) / (30.0 + 70.0);
        assert!((state.imbalance() - expected).abs() < 1e-10);
        assert!(state.imbalance() < 0.0);
    }

    #[rstest]
    fn test_imbalance_zero_when_balanced() {
        let mut state = ImbalanceState::new();
        state.bid_volume_total = 50.0;
        state.ask_volume_total = 50.0;

        assert_eq!(state.imbalance(), 0.0);
    }

    #[rstest]
    fn test_on_book_deltas_accumulates_bid_volume() {
        let id = instrument_a();
        let mut actor = BookImbalanceActor::new(vec![id], 0, None);

        let deltas = make_deltas(
            id,
            vec![
                make_delta(id, OrderSide::Buy, "2.50", "100", 1_000_000),
                make_delta(id, OrderSide::Buy, "2.48", "200", 1_000_000),
            ],
        );
        actor.on_book_deltas(&deltas).unwrap();

        let state = &actor.states()[&id];
        assert_eq!(state.update_count, 1);
        assert!((state.bid_volume_total - 300.0).abs() < 1e-10);
        assert_eq!(state.ask_volume_total, 0.0);
        assert_eq!(state.imbalance(), 1.0);
    }

    #[rstest]
    fn test_on_book_deltas_accumulates_ask_volume() {
        let id = instrument_a();
        let mut actor = BookImbalanceActor::new(vec![id], 0, None);

        let deltas = make_deltas(
            id,
            vec![make_delta(id, OrderSide::Sell, "2.52", "150", 1_000_000)],
        );
        actor.on_book_deltas(&deltas).unwrap();

        let state = &actor.states()[&id];
        assert_eq!(state.ask_volume_total, 150.0);
        assert_eq!(state.imbalance(), -1.0);
    }

    #[rstest]
    fn test_on_book_deltas_mixed_sides() {
        let id = instrument_a();
        let mut actor = BookImbalanceActor::new(vec![id], 0, None);

        let deltas = make_deltas(
            id,
            vec![
                make_delta(id, OrderSide::Buy, "2.50", "80", 1_000_000),
                make_delta(id, OrderSide::Sell, "2.52", "20", 1_000_000),
            ],
        );
        actor.on_book_deltas(&deltas).unwrap();

        let state = &actor.states()[&id];
        assert!((state.bid_volume_total - 80.0).abs() < 1e-10);
        assert!((state.ask_volume_total - 20.0).abs() < 1e-10);

        let expected = (80.0 - 20.0) / (80.0 + 20.0);
        assert!((state.imbalance() - expected).abs() < 1e-10);
    }

    #[rstest]
    fn test_multiple_updates_accumulate() {
        let id = instrument_a();
        let mut actor = BookImbalanceActor::new(vec![id], 0, None);

        let deltas1 = make_deltas(
            id,
            vec![make_delta(id, OrderSide::Buy, "2.50", "100", 1_000_000)],
        );
        let deltas2 = make_deltas(
            id,
            vec![make_delta(id, OrderSide::Sell, "2.52", "60", 2_000_000)],
        );
        let deltas3 = make_deltas(
            id,
            vec![make_delta(id, OrderSide::Buy, "2.50", "40", 3_000_000)],
        );

        actor.on_book_deltas(&deltas1).unwrap();
        actor.on_book_deltas(&deltas2).unwrap();
        actor.on_book_deltas(&deltas3).unwrap();

        let state = &actor.states()[&id];
        assert_eq!(state.update_count, 3);
        assert!((state.bid_volume_total - 140.0).abs() < 1e-10);
        assert!((state.ask_volume_total - 60.0).abs() < 1e-10);
    }

    #[rstest]
    fn test_multiple_instruments_tracked_independently() {
        let id_a = instrument_a();
        let id_b = instrument_b();
        let mut actor = BookImbalanceActor::new(vec![id_a, id_b], 0, None);

        let deltas_a = make_deltas(
            id_a,
            vec![make_delta(id_a, OrderSide::Buy, "2.50", "100", 1_000_000)],
        );
        let deltas_b = make_deltas(
            id_b,
            vec![make_delta(id_b, OrderSide::Sell, "3.00", "200", 1_000_000)],
        );

        actor.on_book_deltas(&deltas_a).unwrap();
        actor.on_book_deltas(&deltas_b).unwrap();

        assert_eq!(actor.states().len(), 2);

        let state_a = &actor.states()[&id_a];
        assert_eq!(state_a.imbalance(), 1.0);

        let state_b = &actor.states()[&id_b];
        assert_eq!(state_b.imbalance(), -1.0);
    }

    #[rstest]
    fn test_unsubscribed_instrument_still_tracked() {
        let id_a = instrument_a();
        let id_b = instrument_b();
        // Actor configured for id_a only, but deltas for id_b still processed
        // (the engine routes data, the actor just handles what it receives)
        let mut actor = BookImbalanceActor::new(vec![id_a], 0, None);

        let deltas_b = make_deltas(
            id_b,
            vec![make_delta(id_b, OrderSide::Buy, "5.00", "50", 1_000_000)],
        );
        actor.on_book_deltas(&deltas_b).unwrap();

        assert!(actor.states().contains_key(&id_b));
    }

    #[rstest]
    fn test_empty_deltas_batch_increments_count() {
        let id = instrument_a();
        let mut actor = BookImbalanceActor::new(vec![id], 0, None);

        // An empty deltas batch (clear action with no orders)
        let delta = OrderBookDelta::clear(id, 0, UnixNanos::from(1u64), UnixNanos::from(1u64));
        let deltas = make_deltas(id, vec![delta]);
        actor.on_book_deltas(&deltas).unwrap();

        let state = &actor.states()[&id];
        assert_eq!(state.update_count, 1);
        assert_eq!(state.bid_volume_total, 0.0);
        assert_eq!(state.ask_volume_total, 0.0);
        assert_eq!(state.imbalance(), 0.0);
    }
}
