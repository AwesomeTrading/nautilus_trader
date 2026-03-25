# How-to Guides

Goal-oriented recipes for common tasks. Each guide assumes familiarity with
Nautilus concepts and focuses on achieving a specific outcome.

New to Nautilus? Start with the [getting started](../getting_started/)
path and [tutorials](../tutorials/) first.

## Data workflows

| Guide                                                 | Description                                    |
|:------------------------------------------------------|:-----------------------------------------------|
| [Loading external data](loading_external_data)        | Load CSV data into the Parquet data catalog.   |
| [Data catalog with Databento](data_catalog_databento) | Set up a catalog with Databento market data.   |

## Live trading

| Guide                                                         | Description                                             |
|:--------------------------------------------------------------|:--------------------------------------------------------|
| [Configure a live trading node](configure_live_trading)       | Set up TradingNodeConfig, execution engine, and venues. |

## Rust

| Guide                                                     | Description                                            |
|:----------------------------------------------------------|:-------------------------------------------------------|
| [Write a Rust actor](write_rust_actor)                    | Build a data actor with subscriptions and handlers.    |
| [Write a Rust strategy](write_rust_strategy)              | Build a strategy with order management.                |
| [Run a backtest in Rust](run_rust_backtest)               | Use BacktestEngine or BacktestNode with a catalog.     |
| [Run live trading in Rust](run_rust_live_trading)         | Connect to a venue with LiveNode.                      |
