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

//! WebSocket message handler for Bybit.

use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};

use nautilus_network::{
    retry::{RetryManager, create_websocket_retry_manager},
    websocket::{AuthTracker, SubscriptionState, WebSocketClient},
};
use tokio_tungstenite::tungstenite::Message;

use super::{
    enums::BybitWsOperation,
    error::{BybitWsError, create_bybit_timeout_error, should_retry_bybit_error},
    messages::{BybitWebSocketError, BybitWsFrame, BybitWsMessage},
    parse::parse_bybit_ws_frame,
};

/// Commands sent from the outer client to the inner message handler.
#[derive(Debug)]
pub enum HandlerCommand {
    SetClient(WebSocketClient),
    Disconnect,
    Authenticate { payload: String },
    Subscribe { topics: Vec<String> },
    Unsubscribe { topics: Vec<String> },
    SendText { payload: String },
}

pub(super) struct BybitWsFeedHandler {
    signal: Arc<AtomicBool>,
    inner: Option<WebSocketClient>,
    cmd_rx: tokio::sync::mpsc::UnboundedReceiver<HandlerCommand>,
    raw_rx: tokio::sync::mpsc::UnboundedReceiver<Message>,
    auth_tracker: AuthTracker,
    subscriptions: SubscriptionState,
    retry_manager: RetryManager<BybitWsError>,
}

impl BybitWsFeedHandler {
    /// Creates a new [`BybitWsFeedHandler`] instance.
    pub(super) fn new(
        signal: Arc<AtomicBool>,
        cmd_rx: tokio::sync::mpsc::UnboundedReceiver<HandlerCommand>,
        raw_rx: tokio::sync::mpsc::UnboundedReceiver<Message>,
        auth_tracker: AuthTracker,
        subscriptions: SubscriptionState,
    ) -> Self {
        Self {
            signal,
            inner: None,
            cmd_rx,
            raw_rx,
            auth_tracker,
            subscriptions,
            retry_manager: create_websocket_retry_manager(),
        }
    }

    pub(super) fn is_stopped(&self) -> bool {
        self.signal.load(Ordering::Relaxed)
    }

    /// Sends a WebSocket message with retry logic.
    async fn send_with_retry(&self, payload: String) -> Result<(), BybitWsError> {
        if let Some(client) = &self.inner {
            self.retry_manager
                .execute_with_retry(
                    "websocket_send",
                    || {
                        let payload = payload.clone();
                        async move {
                            client
                                .send_text(payload, None)
                                .await
                                .map_err(|e| BybitWsError::Transport(format!("Send failed: {e}")))
                        }
                    },
                    should_retry_bybit_error,
                    create_bybit_timeout_error,
                )
                .await
        } else {
            Err(BybitWsError::ClientError(
                "No active WebSocket client".to_string(),
            ))
        }
    }

    pub(super) async fn next(&mut self) -> Option<BybitWsMessage> {
        loop {
            tokio::select! {
                Some(cmd) = self.cmd_rx.recv() => {
                    match cmd {
                        HandlerCommand::SetClient(client) => {
                            log::debug!("WebSocketClient received by handler");
                            self.inner = Some(client);
                        }
                        HandlerCommand::Disconnect => {
                            log::debug!("Disconnect command received");

                            if let Some(client) = self.inner.take() {
                                client.disconnect().await;
                            }
                        }
                        HandlerCommand::Authenticate { payload } => {
                            log::debug!("Authenticate command received");

                            if let Err(e) = self.send_with_retry(payload).await {
                                log::error!("Failed to send authentication after retries: {e}");
                            }
                        }
                        HandlerCommand::Subscribe { topics } => {
                            for topic in topics {
                                log::debug!("Subscribing to topic: topic={topic}");
                                if let Err(e) = self.send_with_retry(topic.clone()).await {
                                    log::error!("Failed to send subscription after retries: topic={topic}, error={e}");
                                }
                            }
                        }
                        HandlerCommand::Unsubscribe { topics } => {
                            for topic in topics {
                                log::debug!("Unsubscribing from topic: topic={topic}");
                                if let Err(e) = self.send_with_retry(topic.clone()).await {
                                    log::error!("Failed to send unsubscription after retries: topic={topic}, error={e}");
                                }
                            }
                        }
                        HandlerCommand::SendText { payload } => {
                            if let Err(e) = self.send_with_retry(payload).await {
                                log::error!("Error sending text with retry: {e}");
                            }
                        }
                    }
                }

                () = tokio::time::sleep(std::time::Duration::from_millis(100)) => {
                    if self.signal.load(Ordering::Relaxed) {
                        log::debug!("Stop signal received during idle period");
                        return None;
                    }
                }

                msg = self.raw_rx.recv() => {
                    let msg = match msg {
                        Some(msg) => msg,
                        None => {
                            log::debug!("WebSocket stream closed");
                            return None;
                        }
                    };

                    if let Message::Ping(data) = &msg {
                        log::trace!("Received ping frame with {} bytes", data.len());

                        if let Some(client) = &self.inner
                            && let Err(e) = client.send_pong(data.to_vec()).await
                        {
                            log::warn!("Failed to send pong frame: error={e}");
                        }
                        continue;
                    }

                    let frame = match Self::parse_raw_frame(msg) {
                        Some(frame) => frame,
                        None => continue,
                    };

                    if self.signal.load(Ordering::Relaxed) {
                        log::debug!("Stop signal received");
                        return None;
                    }

                    match frame {
                        BybitWsFrame::Subscription(ref sub_msg) => {
                            let pending_topics = self.subscriptions.pending_subscribe_topics();
                            match sub_msg.op {
                                BybitWsOperation::Subscribe => {
                                    if sub_msg.success {
                                        for topic in pending_topics {
                                            self.subscriptions.confirm_subscribe(&topic);
                                            log::debug!("Subscription confirmed: topic={topic}");
                                        }
                                    } else {
                                        for topic in pending_topics {
                                            self.subscriptions.mark_failure(&topic);
                                            log::warn!(
                                                "Subscription failed, will retry on reconnect: topic={topic}, error={:?}",
                                                sub_msg.ret_msg
                                            );
                                        }
                                    }
                                }
                                BybitWsOperation::Unsubscribe => {
                                    let pending_unsub = self.subscriptions.pending_unsubscribe_topics();

                                    if sub_msg.success {
                                        for topic in pending_unsub {
                                            self.subscriptions.confirm_unsubscribe(&topic);
                                            log::debug!("Unsubscription confirmed: topic={topic}");
                                        }
                                    } else {
                                        for topic in pending_unsub {
                                            log::warn!(
                                                "Unsubscription failed: topic={topic}, error={:?}",
                                                sub_msg.ret_msg
                                            );
                                        }
                                    }
                                }
                                _ => {}
                            }
                        }
                        BybitWsFrame::Auth(auth_response) => {
                            let is_success = auth_response.success.unwrap_or(false)
                                || (auth_response.ret_code == Some(0));

                            if is_success {
                                self.auth_tracker.succeed();
                                log::info!("WebSocket authenticated");
                            } else {
                                let error_msg = auth_response
                                    .ret_msg
                                    .as_deref()
                                    .unwrap_or("Authentication rejected");
                                self.auth_tracker.fail(error_msg);
                                log::error!("WebSocket authentication failed: error={error_msg}");
                            }
                            return Some(BybitWsMessage::Auth(auth_response));
                        }
                        BybitWsFrame::ErrorResponse(resp) => {
                            let error = BybitWebSocketError::from_response(&resp);
                            return Some(BybitWsMessage::Error(error));
                        }
                        BybitWsFrame::OrderResponse(resp) => {
                            return Some(BybitWsMessage::OrderResponse(resp));
                        }
                        BybitWsFrame::Orderbook(msg) => {
                            return Some(BybitWsMessage::Orderbook(msg));
                        }
                        BybitWsFrame::Trade(msg) => {
                            return Some(BybitWsMessage::Trade(msg));
                        }
                        BybitWsFrame::Kline(msg) => {
                            return Some(BybitWsMessage::Kline(msg));
                        }
                        BybitWsFrame::TickerLinear(msg) => {
                            return Some(BybitWsMessage::TickerLinear(msg));
                        }
                        BybitWsFrame::TickerOption(msg) => {
                            return Some(BybitWsMessage::TickerOption(msg));
                        }
                        BybitWsFrame::AccountOrder(msg) => {
                            return Some(BybitWsMessage::AccountOrder(msg));
                        }
                        BybitWsFrame::AccountExecution(msg) => {
                            return Some(BybitWsMessage::AccountExecution(msg));
                        }
                        BybitWsFrame::AccountWallet(msg) => {
                            return Some(BybitWsMessage::AccountWallet(msg));
                        }
                        BybitWsFrame::AccountPosition(msg) => {
                            return Some(BybitWsMessage::AccountPosition(msg));
                        }
                        BybitWsFrame::Reconnected => {
                            return Some(BybitWsMessage::Reconnected);
                        }
                        BybitWsFrame::Unknown(value) => {
                            log::debug!("Unknown WebSocket frame: {value}");
                        }
                    }
                }
            }
        }
    }

    fn parse_raw_frame(msg: Message) -> Option<BybitWsFrame> {
        match msg {
            Message::Text(text) => {
                if text == nautilus_network::RECONNECTED {
                    log::info!("Received WebSocket reconnected signal");
                    return Some(BybitWsFrame::Reconnected);
                }

                if text.trim().eq_ignore_ascii_case("pong") {
                    return None;
                }

                log::trace!("Raw websocket message: {text}");

                let value: serde_json::Value = match serde_json::from_str(&text) {
                    Ok(v) => v,
                    Err(e) => {
                        log::error!("Failed to parse WebSocket message: {e}: {text}");
                        return None;
                    }
                };

                Some(parse_bybit_ws_frame(value))
            }
            Message::Binary(msg) => {
                log::debug!("Raw binary: {msg:?}");
                None
            }
            Message::Close(_) => {
                log::debug!("Received close message, waiting for reconnection");
                None
            }
            _ => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use rstest::rstest;

    use super::*;
    use crate::common::{consts::BYBIT_WS_TOPIC_DELIMITER, testing::load_test_json};

    fn create_test_handler() -> BybitWsFeedHandler {
        let signal = Arc::new(AtomicBool::new(false));
        let (_cmd_tx, cmd_rx) = tokio::sync::mpsc::unbounded_channel();
        let (_raw_tx, raw_rx) = tokio::sync::mpsc::unbounded_channel();
        let auth_tracker = AuthTracker::new();
        let subscriptions = SubscriptionState::new(BYBIT_WS_TOPIC_DELIMITER);

        BybitWsFeedHandler::new(signal, cmd_rx, raw_rx, auth_tracker, subscriptions)
    }

    fn load_value(fixture: &str) -> serde_json::Value {
        let json = load_test_json(fixture);
        serde_json::from_str(&json).unwrap()
    }

    #[rstest]
    fn test_handler_initializes() {
        let _handler = create_test_handler();
    }

    #[rstest]
    fn test_parse_frame_auth_success() {
        let value = load_value("ws_auth_success.json");
        let frame = parse_bybit_ws_frame(value);
        match frame {
            BybitWsFrame::Auth(auth) => {
                assert_eq!(auth.conn_id.as_deref(), Some("cejreaspqfm9se7usbrg-2xh"));
                assert_eq!(auth.ret_code, Some(0));
                assert_eq!(auth.success, Some(true));
            }
            other => panic!("Expected Auth, was {other:?}"),
        }
    }

    #[rstest]
    fn test_parse_frame_auth_failure() {
        let value = load_value("ws_auth_failure.json");
        let frame = parse_bybit_ws_frame(value);
        match frame {
            BybitWsFrame::ErrorResponse(resp) => {
                assert_eq!(resp.ret_code, Some(10003));
                assert_eq!(resp.ret_msg.as_deref(), Some("Invalid apikey"));
            }
            other => panic!("Expected ErrorResponse, was {other:?}"),
        }
    }

    #[rstest]
    fn test_parse_frame_subscription_ack() {
        let value = load_value("ws_subscription_ack.json");
        let frame = parse_bybit_ws_frame(value);
        match frame {
            BybitWsFrame::Subscription(sub) => {
                assert!(sub.success);
                assert_eq!(sub.op, BybitWsOperation::Subscribe);
                assert_eq!(sub.req_id.as_deref(), Some("sub-orderbook-1"));
            }
            other => panic!("Expected Subscription, was {other:?}"),
        }
    }

    #[rstest]
    fn test_parse_frame_subscription_failure() {
        let value = load_value("ws_subscription_failure.json");
        let frame = parse_bybit_ws_frame(value);
        match frame {
            BybitWsFrame::ErrorResponse(resp) => {
                assert_eq!(
                    resp.ret_msg.as_deref(),
                    Some("Invalid topic: invalid.topic.BTCUSDT")
                );
            }
            other => panic!("Expected ErrorResponse, was {other:?}"),
        }
    }

    #[rstest]
    fn test_parse_frame_order_response() {
        let value = load_value("ws_order_response.json");
        let frame = parse_bybit_ws_frame(value);
        match frame {
            BybitWsFrame::OrderResponse(resp) => {
                assert_eq!(resp.op.as_str(), "order.create");
                assert_eq!(resp.ret_code, 0);
                assert_eq!(resp.ret_msg, "OK");
            }
            other => panic!("Expected OrderResponse, was {other:?}"),
        }
    }

    #[rstest]
    fn test_parse_frame_orderbook() {
        let value = load_value("ws_orderbook_snapshot.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::Orderbook(_)),
            "Expected Orderbook, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_trade() {
        let value = load_value("ws_public_trade.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::Trade(_)),
            "Expected Trade, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_kline() {
        let value = load_value("ws_kline.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::Kline(_)),
            "Expected Kline, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_ticker_linear() {
        let value = load_value("ws_ticker_linear.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::TickerLinear(_)),
            "Expected TickerLinear, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_ticker_option() {
        let value = load_value("ws_ticker_option.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::TickerOption(_)),
            "Expected TickerOption, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_account_order() {
        let value = load_value("ws_account_order.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::AccountOrder(_)),
            "Expected AccountOrder, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_account_execution() {
        let value = load_value("ws_account_execution.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::AccountExecution(_)),
            "Expected AccountExecution, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_account_wallet() {
        let value = load_value("ws_account_wallet.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::AccountWallet(_)),
            "Expected AccountWallet, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_account_position() {
        let value = load_value("ws_account_position.json");
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::AccountPosition(_)),
            "Expected AccountPosition, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_frame_unknown_message() {
        let value: serde_json::Value = serde_json::json!({"foo": "bar"});
        let frame = parse_bybit_ws_frame(value);
        assert!(
            matches!(frame, BybitWsFrame::Unknown(_)),
            "Expected Unknown, was {frame:?}"
        );
    }

    #[rstest]
    fn test_parse_raw_reconnected_signal() {
        let msg = Message::Text(nautilus_network::RECONNECTED.to_string().into());
        let result = BybitWsFeedHandler::parse_raw_frame(msg);
        assert!(
            matches!(result, Some(BybitWsFrame::Reconnected)),
            "Expected Some(Reconnected), was {result:?}"
        );
    }

    #[rstest]
    fn test_parse_raw_pong_text() {
        let msg = Message::Text("pong".into());
        let result = BybitWsFeedHandler::parse_raw_frame(msg);
        assert!(result.is_none(), "Expected None for pong, was {result:?}");
    }

    #[rstest]
    fn test_parse_raw_valid_json() {
        let json = load_test_json("ws_public_trade.json");
        let msg = Message::Text(json.into());
        let result = BybitWsFeedHandler::parse_raw_frame(msg);
        assert!(
            matches!(result, Some(BybitWsFrame::Trade(_))),
            "Expected Some(Trade), was {result:?}"
        );
    }

    #[rstest]
    fn test_parse_raw_invalid_json() {
        let msg = Message::Text("not valid json".into());
        let result = BybitWsFeedHandler::parse_raw_frame(msg);
        assert!(
            result.is_none(),
            "Expected None for invalid JSON, was {result:?}"
        );
    }

    #[rstest]
    fn test_parse_raw_binary_message() {
        let msg = Message::Binary(vec![0x01, 0x02].into());
        let result = BybitWsFeedHandler::parse_raw_frame(msg);
        assert!(result.is_none(), "Expected None for binary, was {result:?}");
    }
}
