# Betfair v2

The Betfair Rust adapter is in active parity work. This page tracks the current Rust behavior and
the planned cutover from the stable guide in [Betfair](betfair.md).

This page mirrors the main section order from [Betfair](betfair.md). When the Rust adapter becomes
the primary Betfair path, this file can replace `betfair.md` with small edits instead of a full
rewrite.

## Scope

- Source of truth for this page: `crates/adapters/betfair`
- Stable guide today: [Betfair](betfair.md)
- Purpose of this page: track the current Rust surface, the known gaps, and the cutover path

## Current Rust status

| Area                         | Current Rust behavior                                                                 | Difference from `betfair.md` today                                         | Cutover work |
|------------------------------|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------|--------------|
| Order types                  | `MARKET` only supports `AT_THE_CLOSE`; `LIMIT` supports BSP on close flows            | Stable guide is still Python shaped in this area                            | Decide final Betfair market order model |
| Batch operations             | `SubmitOrderList` and `BatchCancelOrders` are implemented                             | Stable guide used to mark these as unsupported                              | Keep and promote |
| Reconciliation scope         | `reconcile_market_ids_only` uses `reconcile_market_ids`; otherwise Rust falls back to `stream_market_ids_filter` | Stable guide says stream filtering and reconciliation are separate          | Decide if Rust keeps or removes this coupling |
| Full image cache checks      | Rust uses `generate_mass_status()` at startup and does not run `check_cache_against_order_image` | Stable guide describes the Python full image cache check                    | Add parity or document the Rust path as final |
| External order filtering     | `ignore_external_orders` only skips OCM updates with no `rfo`                         | Python also uses it during full image cache checks                          | Decide final filtering behavior |
| Config surface               | No `certs_dir`, no `instrument_config`, fixed keep alive, required heartbeat value    | Stable guide still documents the Python config surface                      | Decide whether to add parity or bless the Rust surface |
| SSL certificates             | Stream client currently hardcodes `certs_dir=None`                                    | Stable guide documents certificate configuration and `BETFAIR_CERTS_DIR`    | Add support or remove from the future guide |

## Orders capability

### Order types

| Order Type             | Supported | Notes |
|------------------------|-----------|-------|
| `MARKET`               | ✓*        | Rust only supports `AT_THE_CLOSE`, which maps to Betfair `MARKET_ON_CLOSE`. |
| `LIMIT`                | ✓         | Rust supports regular limit orders and BSP on close limit orders. |
| `STOP_MARKET`          | -         | Not supported. |
| `STOP_LIMIT`           | -         | Not supported. |
| `MARKET_IF_TOUCHED`    | -         | Not supported. |
| `LIMIT_IF_TOUCHED`     | -         | Not supported. |
| `TRAILING_STOP_MARKET` | -         | Not supported. |

### Time in force

| Time in force   | Supported | Notes |
|-----------------|-----------|-------|
| `GTC`           | ✓         | Maps to Betfair `PERSIST`. |
| `DAY`           | ✓         | Maps to Betfair `LAPSE`. |
| `FOK`           | ✓         | Maps to Betfair `FILL_OR_KILL`. |
| `IOC`           | ✓         | Maps to `FILL_OR_KILL` with `min_fill_size=0`. |
| `AT_THE_CLOSE`  | ✓         | Used for Betfair BSP `LIMIT_ON_CLOSE` and `MARKET_ON_CLOSE`. |

Rust currently also accepts `LIMIT` orders in `AT_THE_OPEN` mode and routes them through Betfair
`LIMIT_ON_CLOSE` instructions. Treat that as current behavior, not a settled public contract.

### Batch operations

| Operation      | Supported | Notes |
|----------------|-----------|-------|
| Batch Submit   | ✓         | Implemented through `SubmitOrderList`. |
| Batch Modify   | -         | Not supported. |
| Batch Cancel   | ✓         | Implemented through `BatchCancelOrders`. |

## Execution control flow

The current Rust execution path is:

1. Connect the HTTP client and fetch initial account funds.
2. Seed OCM state from cached orders.
3. Connect the Betfair execution stream and subscribe to order updates.
4. Generate startup mass status from `listCurrentOrders`.
5. Reconcile order and fill reports into the execution engine.

Current Rust notes:

- `stream_market_ids_filter` filters live OCM updates.
- `reconcile_market_ids_only=True` uses explicit `reconcile_market_ids`.
- When `reconcile_market_ids_only=False` and `reconcile_market_ids` is unset, Rust currently
  falls back to `stream_market_ids_filter` for startup reconciliation.
- Rust does not yet implement the Python `check_cache_against_order_image` full-image cache check.
- `ignore_external_orders=True` currently skips only OCM updates with no `rfo`.

## Current Rust configuration

### Data client configuration

| Option                             | Default   | Notes |
|------------------------------------|-----------|-------|
| `account_currency`                 | Required  | Betfair account currency. |
| `username`                         | `None`    | Falls back to `BETFAIR_USERNAME`. |
| `password`                         | `None`    | Falls back to `BETFAIR_PASSWORD`. |
| `app_key`                          | `None`    | Falls back to `BETFAIR_APP_KEY`. |
| `proxy_url`                        | `None`    | Optional HTTP proxy. |
| `request_rate_per_second`          | `5`       | General HTTP rate limit. |
| `default_min_notional`             | `None`    | Optional minimum notional override. |
| `event_type_ids`                   | `None`    | Optional navigation filter. |
| `event_type_names`                 | `None`    | Optional navigation filter. |
| `event_ids`                        | `None`    | Optional navigation filter. |
| `country_codes`                    | `None`    | Optional navigation filter. |
| `market_types`                     | `None`    | Optional navigation filter. |
| `market_ids`                       | `None`    | Optional navigation filter. |
| `min_market_start_time`            | `None`    | Optional navigation filter. |
| `max_market_start_time`            | `None`    | Optional navigation filter. |
| `stream_host`                      | `None`    | Optional stream host override. |
| `stream_port`                      | `None`    | Optional stream port override. |
| `stream_heartbeat_ms`              | `5,000`   | Required in Rust today. |
| `stream_idle_timeout_ms`           | `60,000`  | Idle timeout before reconnect. |
| `stream_reconnect_delay_initial_ms`| `2,000`   | Initial reconnect delay. |
| `stream_reconnect_delay_max_ms`    | `30,000`  | Maximum reconnect delay. |
| `stream_use_tls`                   | `True`    | Use TLS for the stream connection. |
| `stream_conflate_ms`               | `None`    | Explicit conflation setting. |
| `subscription_delay_secs`          | `3`       | Delay before the first market subscription. |
| `subscribe_race_data`              | `False`   | Subscribe to RCM updates. |

Rust does not yet expose `certs_dir` or `instrument_config`. Rust also uses a fixed 36,000 second
keep-alive interval.

### Execution client configuration

| Option                             | Default   | Notes |
|------------------------------------|-----------|-------|
| `trader_id`                        | `TRADER-001` | Trader ID for the client core. |
| `account_id`                       | `BETFAIR-001` | Account ID for the client core. |
| `account_currency`                 | `GBP`     | Betfair account currency. |
| `username`                         | `None`    | Falls back to `BETFAIR_USERNAME`. |
| `password`                         | `None`    | Falls back to `BETFAIR_PASSWORD`. |
| `app_key`                          | `None`    | Falls back to `BETFAIR_APP_KEY`. |
| `proxy_url`                        | `None`    | Optional HTTP proxy. |
| `request_rate_per_second`          | `5`       | General HTTP rate limit. |
| `order_request_rate_per_second`    | `20`      | Order endpoint rate limit. |
| `stream_host`                      | `None`    | Optional stream host override. |
| `stream_port`                      | `None`    | Optional stream port override. |
| `stream_heartbeat_ms`              | `5,000`   | Required in Rust today. |
| `stream_idle_timeout_ms`           | `60,000`  | Idle timeout before reconnect. |
| `stream_reconnect_delay_initial_ms`| `2,000`   | Initial reconnect delay. |
| `stream_reconnect_delay_max_ms`    | `30,000`  | Maximum reconnect delay. |
| `stream_use_tls`                   | `True`    | Use TLS for the stream connection. |
| `stream_market_ids_filter`         | `None`    | Optional live OCM market filter. |
| `ignore_external_orders`           | `False`   | Only skips OCM updates with no `rfo`. |
| `calculate_account_state`          | `True`    | Gates periodic account state polling in Rust today. |
| `request_account_state_secs`       | `300`     | Poll interval for account funds. |
| `reconcile_market_ids_only`        | `False`   | When `True`, use `reconcile_market_ids`. |
| `reconcile_market_ids`             | `None`    | Explicit startup reconciliation market IDs. |
| `use_market_version`               | `False`   | Attach market version to place and replace requests. |

Rust does not yet expose `certs_dir` or `instrument_config`.

## Cutover plan

Use this page as the transition tracker until the Rust adapter becomes the primary Betfair path.

At cutover:

1. Decide whether Rust keeps its current reconciliation filter behavior or matches the Python split.
2. Decide whether Rust adds certificate configuration and other Python config fields.
3. Decide whether Rust keeps BSP-only `MARKET` orders or adds the Python aggressive-limit path.
4. Promote this file to `betfair.md`.
5. Move any remaining Python-only notes into a short legacy note or release note.
