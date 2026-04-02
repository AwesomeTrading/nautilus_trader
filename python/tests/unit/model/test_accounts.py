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

from nautilus_trader.core import UUID4
from nautilus_trader.model import AccountBalance
from nautilus_trader.model import AccountId
from nautilus_trader.model import AccountState
from nautilus_trader.model import AccountType
from nautilus_trader.model import BettingAccount
from nautilus_trader.model import CashAccount
from nautilus_trader.model import Currency
from nautilus_trader.model import LeveragedMarginModel
from nautilus_trader.model import MarginAccount
from nautilus_trader.model import MarginBalance
from nautilus_trader.model import Money
from nautilus_trader.model import StandardMarginModel
from nautilus_trader.model import betting_account_from_account_events
from nautilus_trader.model import cash_account_from_account_events
from nautilus_trader.model import margin_account_from_account_events
from tests.providers import TestInstrumentProvider


def test_cash_account_properties_and_balances():
    usd = Currency.from_str("USD")
    balance = AccountBalance(
        total=Money.from_str("1000.00 USD"),
        locked=Money.from_str("100.00 USD"),
        free=Money.from_str("900.00 USD"),
    )
    state = AccountState(
        account_id=AccountId("SIM-001"),
        account_type=AccountType.CASH,
        balances=[balance],
        margins=[],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=usd,
    )

    account = CashAccount(state, calculate_account_state=True, allow_borrowing=True)

    assert account.id == AccountId("SIM-001")
    assert account.account_type == AccountType.CASH
    assert account.base_currency == usd
    assert account.allow_borrowing is True
    assert account.calculate_account_state is True
    assert account.event_count == 1
    assert account.balance_total() == Money.from_str("1000.00 USD")
    assert account.balance_free() == Money.from_str("900.00 USD")
    assert account.balance_locked() == Money.from_str("100.00 USD")
    assert account.to_dict()["events"][0]["type"] == "AccountState"


def test_cash_account_apply_updates_balances():
    usd = Currency.from_str("USD")
    initial = AccountState(
        account_id=AccountId("SIM-001"),
        account_type=AccountType.CASH,
        balances=[
            AccountBalance(
                total=Money.from_str("1000.00 USD"),
                locked=Money.from_str("100.00 USD"),
                free=Money.from_str("900.00 USD"),
            ),
        ],
        margins=[],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=usd,
    )
    updated = AccountState(
        account_id=AccountId("SIM-001"),
        account_type=AccountType.CASH,
        balances=[
            AccountBalance(
                total=Money.from_str("1200.00 USD"),
                locked=Money.from_str("150.00 USD"),
                free=Money.from_str("1050.00 USD"),
            ),
        ],
        margins=[],
        is_reported=True,
        event_id=UUID4(),
        ts_event=3,
        ts_init=4,
        base_currency=usd,
    )

    account = CashAccount(initial, calculate_account_state=True)
    account.apply(updated)

    assert account.event_count == 2
    assert account.balance_total() == Money.from_str("1200.00 USD")
    assert account.balance_free() == Money.from_str("1050.00 USD")
    assert account.balance_locked() == Money.from_str("150.00 USD")


def test_margin_account_properties_and_updates():
    instrument = TestInstrumentProvider.audusd_sim()
    usd = Currency.from_str("USD")
    state = AccountState(
        account_id=AccountId("SIM-002"),
        account_type=AccountType.MARGIN,
        balances=[
            AccountBalance(
                total=Money.from_str("1000.00 USD"),
                locked=Money.from_str("100.00 USD"),
                free=Money.from_str("900.00 USD"),
            ),
        ],
        margins=[
            MarginBalance(
                initial=Money.from_str("10.00 USD"),
                maintenance=Money.from_str("5.00 USD"),
                instrument=instrument.id,
            ),
        ],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=usd,
    )

    account = MarginAccount(state, calculate_account_state=True)
    account.set_default_leverage(Decimal(3))
    account.set_leverage(instrument.id, Decimal(5))
    account.update_initial_margin(instrument.id, Money.from_str("12.00 USD"))
    account.update_maintenance_margin(instrument.id, Money.from_str("6.00 USD"))

    assert account.id == AccountId("SIM-002")
    assert account.default_leverage == Decimal(3)
    assert account.leverage(instrument.id) == Decimal(5)
    assert account.initial_margin(instrument.id) == Money.from_str("12.00 USD")
    assert account.maintenance_margin(instrument.id) == Money.from_str("6.00 USD")
    assert account.is_unleveraged(instrument.id) is False
    assert account.to_dict()["events"][0]["account_type"] == "MARGIN"


def test_cash_account_from_account_events():
    state = AccountState(
        account_id=AccountId("SIM-003"),
        account_type=AccountType.CASH,
        balances=[
            AccountBalance(
                total=Money.from_str("1000.00 USD"),
                locked=Money.from_str("100.00 USD"),
                free=Money.from_str("900.00 USD"),
            ),
        ],
        margins=[],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=Currency.from_str("USD"),
    )

    account = cash_account_from_account_events(
        [state.to_dict()],
        calculate_account_state=True,
        allow_borrowing=True,
    )

    assert account.id == AccountId("SIM-003")
    assert account.balance_free() == Money.from_str("900.00 USD")
    assert account.allow_borrowing is True


def test_margin_account_from_account_events():
    instrument = TestInstrumentProvider.audusd_sim()
    state = AccountState(
        account_id=AccountId("SIM-004"),
        account_type=AccountType.MARGIN,
        balances=[
            AccountBalance(
                total=Money.from_str("1000.00 USD"),
                locked=Money.from_str("100.00 USD"),
                free=Money.from_str("900.00 USD"),
            ),
        ],
        margins=[
            MarginBalance(
                initial=Money.from_str("10.00 USD"),
                maintenance=Money.from_str("5.00 USD"),
                instrument=instrument.id,
            ),
        ],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=Currency.from_str("USD"),
    )

    account = margin_account_from_account_events(
        [state.to_dict()],
        calculate_account_state=True,
    )

    assert account.id == AccountId("SIM-004")
    assert account.initial_margin(instrument.id) == Money.from_str("10.00 USD")
    assert account.maintenance_margin(instrument.id) == Money.from_str("5.00 USD")


def test_margin_model_exports():
    assert type(StandardMarginModel()).__name__ == "StandardMarginModel"
    assert type(LeveragedMarginModel()).__name__ == "LeveragedMarginModel"


def test_betting_account_properties():
    state = AccountState(
        account_id=AccountId("SIM-005"),
        account_type=AccountType.BETTING,
        balances=[
            AccountBalance(
                total=Money.from_str("1000.00 USD"),
                locked=Money.from_str("125.00 USD"),
                free=Money.from_str("875.00 USD"),
            ),
        ],
        margins=[],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=Currency.from_str("USD"),
    )

    account = BettingAccount(state, calculate_account_state=True)

    assert account.id == AccountId("SIM-005")
    assert account.account_type == AccountType.BETTING
    assert account.balance_locked() == Money.from_str("125.00 USD")


def test_betting_account_from_account_events():
    state = AccountState(
        account_id=AccountId("SIM-006"),
        account_type=AccountType.BETTING,
        balances=[
            AccountBalance(
                total=Money.from_str("1000.00 USD"),
                locked=Money.from_str("125.00 USD"),
                free=Money.from_str("875.00 USD"),
            ),
        ],
        margins=[],
        is_reported=True,
        event_id=UUID4(),
        ts_event=1,
        ts_init=2,
        base_currency=Currency.from_str("USD"),
    )

    account = betting_account_from_account_events(
        [state.to_dict()],
        calculate_account_state=True,
    )

    assert account.id == AccountId("SIM-006")
    assert account.balance_free() == Money.from_str("875.00 USD")
