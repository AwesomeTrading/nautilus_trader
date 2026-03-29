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

use std::fmt::{Debug, Display};

use derive_builder::Builder;
use nautilus_core::{UUID4, UnixNanos, serialization::from_bool_as_u8};
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};
use ustr::Ustr;

use crate::{
    enums::{
        ContingencyType, LiquiditySide, OrderSide, OrderType, TimeInForce, TrailingOffsetType,
        TriggerType,
    },
    events::OrderEvent,
    identifiers::{
        AccountId, ClientOrderId, ExecAlgorithmId, InstrumentId, OrderListId, PositionId,
        StrategyId, TradeId, TraderId, VenueOrderId,
    },
    types::{Currency, Money, Price, Quantity},
};

/// Represents an event where an order has been canceled at the trading venue.
#[repr(C)]
#[derive(Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Builder)]
#[serde(tag = "type")]
#[cfg_attr(any(test, feature = "stubs"), builder(default))]
#[cfg_attr(
    feature = "python",
    pyo3::pyclass(module = "nautilus_trader.core.nautilus_pyo3.model", from_py_object)
)]
#[cfg_attr(
    feature = "python",
    pyo3_stub_gen::derive::gen_stub_pyclass(module = "nautilus_trader.model")
)]
pub struct OrderCanceled {
    /// The trader ID associated with the event.
    pub trader_id: TraderId,
    /// The strategy ID associated with the event.
    pub strategy_id: StrategyId,
    /// The instrument ID associated with the event.
    pub instrument_id: InstrumentId,
    /// The client order ID associated with the event.
    pub client_order_id: ClientOrderId,
    /// The unique identifier for the event.
    pub event_id: UUID4,
    /// UNIX timestamp (nanoseconds) when the event occurred.
    pub ts_event: UnixNanos,
    /// UNIX timestamp (nanoseconds) when the event was initialized.
    pub ts_init: UnixNanos,
    /// If the event was generated during reconciliation.
    #[serde(deserialize_with = "from_bool_as_u8")]
    pub reconciliation: u8, // TODO: Change to bool once Cython removed
    /// The venue order ID associated with the event.
    pub venue_order_id: Option<VenueOrderId>,
    /// The account ID associated with the event.
    pub account_id: Option<AccountId>,
}

impl OrderCanceled {
    /// Creates a new [`OrderCanceled`] instance.
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        trader_id: TraderId,
        strategy_id: StrategyId,
        instrument_id: InstrumentId,
        client_order_id: ClientOrderId,
        event_id: UUID4,
        ts_event: UnixNanos,
        ts_init: UnixNanos,
        reconciliation: bool,
        venue_order_id: Option<VenueOrderId>,
        account_id: Option<AccountId>,
    ) -> Self {
        Self {
            trader_id,
            strategy_id,
            instrument_id,
            client_order_id,
            event_id,
            ts_event,
            ts_init,
            reconciliation: u8::from(reconciliation),
            venue_order_id,
            account_id,
        }
    }
}

impl Debug for OrderCanceled {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}(trader_id={}, strategy_id={}, instrument_id={}, client_order_id={}, venue_order_id={}, account_id={}, event_id={}, ts_event={}, ts_init={})",
            stringify!(OrderCanceled),
            self.trader_id,
            self.strategy_id,
            self.instrument_id,
            self.client_order_id,
            self.venue_order_id.map_or_else(
                || "None".to_string(),
                |venue_order_id| format!("{venue_order_id}")
            ),
            self.account_id
                .map_or_else(|| "None".to_string(), |account_id| format!("{account_id}")),
            self.event_id,
            self.ts_event,
            self.ts_init
        )
    }
}

impl Display for OrderCanceled {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "{}(instrument_id={}, client_order_id={}, venue_order_id={}, account_id={}, ts_event={})",
            stringify!(OrderCanceled),
            self.instrument_id,
            self.client_order_id,
            self.venue_order_id
                .map_or("None".to_string(), |venue_order_id| format!(
                    "{venue_order_id}"
                )),
            self.account_id
                .map_or("None".to_string(), |account_id| format!("{account_id}")),
            self.ts_event
        )
    }
}

impl OrderEvent for OrderCanceled {
    fn id(&self) -> UUID4 {
        self.event_id
    }

    fn type_name(&self) -> &'static str {
        stringify!(OrderCanceled)
    }

    fn order_type(&self) -> Option<OrderType> {
        None
    }

    fn order_side(&self) -> Option<OrderSide> {
        None
    }

    fn trader_id(&self) -> TraderId {
        self.trader_id
    }

    fn strategy_id(&self) -> StrategyId {
        self.strategy_id
    }

    fn instrument_id(&self) -> InstrumentId {
        self.instrument_id
    }

    fn trade_id(&self) -> Option<TradeId> {
        None
    }

    fn currency(&self) -> Option<Currency> {
        None
    }

    fn client_order_id(&self) -> ClientOrderId {
        self.client_order_id
    }

    fn reason(&self) -> Option<Ustr> {
        None
    }

    fn quantity(&self) -> Option<Quantity> {
        None
    }

    fn time_in_force(&self) -> Option<TimeInForce> {
        None
    }

    fn liquidity_side(&self) -> Option<LiquiditySide> {
        None
    }

    fn post_only(&self) -> Option<bool> {
        None
    }

    fn reduce_only(&self) -> Option<bool> {
        None
    }

    fn quote_quantity(&self) -> Option<bool> {
        None
    }

    fn reconciliation(&self) -> bool {
        false
    }

    fn price(&self) -> Option<Price> {
        None
    }

    fn last_px(&self) -> Option<Price> {
        None
    }

    fn last_qty(&self) -> Option<Quantity> {
        None
    }

    fn trigger_price(&self) -> Option<Price> {
        None
    }

    fn trigger_type(&self) -> Option<TriggerType> {
        None
    }

    fn limit_offset(&self) -> Option<Decimal> {
        None
    }

    fn trailing_offset(&self) -> Option<Decimal> {
        None
    }

    fn trailing_offset_type(&self) -> Option<TrailingOffsetType> {
        None
    }

    fn expire_time(&self) -> Option<UnixNanos> {
        None
    }

    fn display_qty(&self) -> Option<Quantity> {
        None
    }

    fn emulation_trigger(&self) -> Option<TriggerType> {
        None
    }

    fn trigger_instrument_id(&self) -> Option<InstrumentId> {
        None
    }

    fn contingency_type(&self) -> Option<ContingencyType> {
        None
    }

    fn order_list_id(&self) -> Option<OrderListId> {
        None
    }

    fn linked_order_ids(&self) -> Option<Vec<ClientOrderId>> {
        None
    }

    fn parent_order_id(&self) -> Option<ClientOrderId> {
        None
    }

    fn exec_algorithm_id(&self) -> Option<ExecAlgorithmId> {
        None
    }

    fn exec_spawn_id(&self) -> Option<ClientOrderId> {
        None
    }

    fn venue_order_id(&self) -> Option<VenueOrderId> {
        self.venue_order_id
    }

    fn account_id(&self) -> Option<AccountId> {
        self.account_id
    }

    fn position_id(&self) -> Option<PositionId> {
        None
    }

    fn commission(&self) -> Option<Money> {
        None
    }

    fn ts_event(&self) -> UnixNanos {
        self.ts_event
    }

    fn ts_init(&self) -> UnixNanos {
        self.ts_init
    }
}

#[cfg(test)]
mod tests {
    use nautilus_core::{UUID4, UnixNanos};
    use rstest::rstest;

    use super::*;
    use crate::{
        identifiers::{AccountId, ClientOrderId, InstrumentId, StrategyId, TraderId, VenueOrderId},
        stubs::TestDefault,
    };

    fn create_test_order_canceled() -> OrderCanceled {
        OrderCanceled::new(
            TraderId::from("TRADER-001"),
            StrategyId::from("EMA-CROSS"),
            InstrumentId::from("EURUSD.SIM"),
            ClientOrderId::from("O-19700101-000000-001-001-1"),
            UUID4::default(),
            UnixNanos::from(1_000_000_000),
            UnixNanos::from(2_000_000_000),
            false,
            Some(VenueOrderId::from("V-001")),
            Some(AccountId::from("SIM-001")),
        )
    }

    #[rstest]
    fn test_order_canceled_new() {
        let order_canceled = create_test_order_canceled();

        assert_eq!(order_canceled.trader_id, TraderId::from("TRADER-001"));
        assert_eq!(order_canceled.strategy_id, StrategyId::from("EMA-CROSS"));
        assert_eq!(
            order_canceled.instrument_id,
            InstrumentId::from("EURUSD.SIM")
        );
        assert_eq!(
            order_canceled.client_order_id,
            ClientOrderId::from("O-19700101-000000-001-001-1")
        );
        assert_eq!(
            order_canceled.venue_order_id,
            Some(VenueOrderId::from("V-001"))
        );
        assert_eq!(order_canceled.account_id, Some(AccountId::from("SIM-001")));
        assert_eq!(order_canceled.ts_event, UnixNanos::from(1_000_000_000));
        assert_eq!(order_canceled.ts_init, UnixNanos::from(2_000_000_000));
        assert_eq!(order_canceled.reconciliation, 0);
    }

    #[rstest]
    fn test_order_canceled_new_with_reconciliation() {
        let order_canceled = OrderCanceled::new(
            TraderId::from("TRADER-001"),
            StrategyId::from("EMA-CROSS"),
            InstrumentId::from("EURUSD.SIM"),
            ClientOrderId::from("O-19700101-000000-001-001-1"),
            UUID4::default(),
            UnixNanos::from(1_000_000_000),
            UnixNanos::from(2_000_000_000),
            true,
            None,
            None,
        );

        assert_eq!(order_canceled.reconciliation, 1);
    }

    #[rstest]
    fn test_order_canceled_display() {
        let order_canceled = create_test_order_canceled();
        let display = format!("{order_canceled}");
        assert!(display.starts_with("OrderCanceled("));
        assert!(display.contains("instrument_id=EURUSD.SIM"));
        assert!(display.contains("client_order_id=O-19700101-000000-001-001-1"));
        assert!(display.contains("venue_order_id=V-001"));
        assert!(display.contains("account_id=SIM-001"));
    }

    #[rstest]
    fn test_order_canceled_default() {
        let order_canceled = OrderCanceled::default();

        assert_eq!(order_canceled.trader_id, TraderId::test_default());
        assert_eq!(order_canceled.strategy_id, StrategyId::test_default());
        assert_eq!(order_canceled.instrument_id, InstrumentId::test_default());
        assert_eq!(
            order_canceled.client_order_id,
            ClientOrderId::test_default()
        );
        assert_eq!(order_canceled.venue_order_id, None);
        assert_eq!(order_canceled.account_id, None);
        assert_eq!(order_canceled.reconciliation, 0);
    }

    #[rstest]
    fn test_order_canceled_order_event_trait() {
        let order_canceled = create_test_order_canceled();

        assert_eq!(order_canceled.id(), order_canceled.event_id);
        assert_eq!(order_canceled.type_name(), "OrderCanceled");
        assert_eq!(order_canceled.order_type(), None);
        assert_eq!(order_canceled.order_side(), None);
        assert_eq!(order_canceled.trader_id(), TraderId::from("TRADER-001"));
        assert_eq!(order_canceled.strategy_id(), StrategyId::from("EMA-CROSS"));
        assert_eq!(
            order_canceled.instrument_id(),
            InstrumentId::from("EURUSD.SIM")
        );
        assert_eq!(order_canceled.trade_id(), None);
        assert_eq!(order_canceled.currency(), None);
        assert_eq!(
            order_canceled.client_order_id(),
            ClientOrderId::from("O-19700101-000000-001-001-1")
        );
        assert_eq!(order_canceled.reason(), None);
        assert_eq!(order_canceled.quantity(), None);
        assert_eq!(order_canceled.time_in_force(), None);
        assert_eq!(order_canceled.liquidity_side(), None);
        assert_eq!(order_canceled.post_only(), None);
        assert_eq!(order_canceled.reduce_only(), None);
        assert_eq!(order_canceled.quote_quantity(), None);
        assert!(!order_canceled.reconciliation());
        assert_eq!(
            order_canceled.venue_order_id(),
            Some(VenueOrderId::from("V-001"))
        );
        assert_eq!(
            order_canceled.account_id(),
            Some(AccountId::from("SIM-001"))
        );
        assert_eq!(order_canceled.position_id(), None);
        assert_eq!(order_canceled.commission(), None);
        assert_eq!(order_canceled.ts_event(), UnixNanos::from(1_000_000_000));
        assert_eq!(order_canceled.ts_init(), UnixNanos::from(2_000_000_000));
    }

    #[rstest]
    fn test_order_canceled_debug() {
        let order_canceled = create_test_order_canceled();
        let debug_str = format!("{order_canceled:?}");

        assert!(debug_str.contains("OrderCanceled"));
        assert!(debug_str.contains("TRADER-001"));
        assert!(debug_str.contains("EMA-CROSS"));
        assert!(debug_str.contains("EURUSD.SIM"));
        assert!(debug_str.contains("O-19700101-000000-001-001-1"));
    }

    #[rstest]
    fn test_order_canceled_partial_eq() {
        let order_canceled1 = create_test_order_canceled();
        let mut order_canceled2 = create_test_order_canceled();
        order_canceled2.event_id = order_canceled1.event_id;
        let mut order_canceled3 = create_test_order_canceled();
        order_canceled3.venue_order_id = Some(VenueOrderId::from("V-002"));

        assert_eq!(order_canceled1, order_canceled2);
        assert_ne!(order_canceled1, order_canceled3);
    }

    #[rstest]
    fn test_order_canceled_timestamps() {
        let order_canceled = create_test_order_canceled();

        assert_eq!(order_canceled.ts_event, UnixNanos::from(1_000_000_000));
        assert_eq!(order_canceled.ts_init, UnixNanos::from(2_000_000_000));
        assert!(order_canceled.ts_event < order_canceled.ts_init);
    }

    #[rstest]
    fn test_order_canceled_serialization() {
        let original = create_test_order_canceled();

        let json = serde_json::to_string(&original).unwrap();
        let deserialized: OrderCanceled = serde_json::from_str(&json).unwrap();

        assert_eq!(original, deserialized);
    }
}
