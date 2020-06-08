# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2020 Nautech Systems Pty Ltd. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE file.
#  https://nautechsystems.io
# -------------------------------------------------------------------------------------------------

import unittest
import uuid

from nautilus_trader.core.types import GUID, ValidString
from nautilus_trader.core.decimal import Decimal
from nautilus_trader.model.enums import Currency
from nautilus_trader.model.objects import Money
from nautilus_trader.model.events import AccountStateEvent
from nautilus_trader.model.identifiers import Brokerage, AccountNumber, AccountId
from nautilus_trader.common.account import Account
from tests.test_kit.stubs import UNIX_EPOCH


class AccountTests(unittest.TestCase):

    def test_can_initialize_account_with_event(self):
        # Arrange
        event = AccountStateEvent(
            AccountId.py_from_string('FXCM-123456-SIMULATED'),
            Currency.AUD,
            Money(1000000, Currency.AUD),
            Money(1000000, Currency.AUD),
            Money(0, Currency.AUD),
            Money(0, Currency.AUD),
            Money(0, Currency.AUD),
            Decimal(0),
            ValidString('N'),
            GUID(uuid.uuid4()),
            UNIX_EPOCH)

        # Act
        account = Account(event)

        # Assert
        self.assertEqual(AccountId.py_from_string('FXCM-123456-SIMULATED'), account.id)
        self.assertEqual(Currency.AUD, account.currency)
        self.assertEqual(Money(1000000, Currency.AUD), account.free_equity)
        self.assertEqual(Money(1000000, Currency.AUD), account.cash_start_day)
        self.assertEqual(Money(0, Currency.AUD), account.cash_activity_day)
        self.assertEqual(Money(0, Currency.AUD), account.margin_used_liquidation)
        self.assertEqual(Money(0, Currency.AUD), account.margin_used_maintenance)
        self.assertEqual(Decimal(0), account.margin_ratio)
        self.assertEqual('N', account.margin_call_status.value)
        self.assertEqual(UNIX_EPOCH, account.last_updated)

    def test_can_calculate_free_equity_when_greater_than_zero(self):
        # Arrange
        event = AccountStateEvent(
            AccountId.py_from_string('FXCM-123456-SIMULATED'),
            Currency.AUD,
            Money(100000, Currency.AUD),
            Money(100000, Currency.AUD),
            Money(0, Currency.AUD),
            Money(1000, Currency.AUD),
            Money(2000, Currency.AUD),
            Decimal(0),
            ValidString('N'),
            GUID(uuid.uuid4()),
            UNIX_EPOCH)

        # Act
        account = Account(event)

        # Assert
        self.assertEqual(AccountId.py_from_string('FXCM-123456-SIMULATED'), account.id)
        self.assertEqual(Brokerage('FXCM'), account.broker)
        self.assertEqual(AccountNumber('123456'), account.account_number)
        self.assertEqual(Currency.AUD, account.currency)
        self.assertEqual(Money(97000, Currency.AUD), account.free_equity)
        self.assertEqual(Money(100000, Currency.AUD), account.cash_start_day)
        self.assertEqual(Money(0, Currency.AUD), account.cash_activity_day)
        self.assertEqual(Money(1000, Currency.AUD), account.margin_used_liquidation)
        self.assertEqual(Money(2000, Currency.AUD), account.margin_used_maintenance)
        self.assertEqual(Decimal(0), account.margin_ratio)
        self.assertEqual('N', account.margin_call_status.value)
        self.assertEqual(UNIX_EPOCH, account.last_updated)

    def test_can_calculate_free_equity_when_zero(self):
        # Arrange
        event = AccountStateEvent(
            AccountId.py_from_string('FXCM-123456-SIMULATED'),
            Currency.AUD,
            Money(20000, Currency.AUD),
            Money(100000, Currency.AUD),
            Money(0, Currency.AUD),
            Money(0, Currency.AUD),
            Money(20000, Currency.AUD),
            Decimal(0),
            ValidString('N'),
            GUID(uuid.uuid4()),
            UNIX_EPOCH)

        # Act
        account = Account(event)

        # Assert
        self.assertEqual(AccountId.py_from_string('FXCM-123456-SIMULATED'), account.id)
        self.assertEqual(Brokerage('FXCM'), account.broker)
        self.assertEqual(AccountNumber('123456'), account.account_number)
        self.assertEqual(Currency.AUD, account.currency)
        self.assertEqual(Money(0, Currency.AUD), account.free_equity)
        self.assertEqual(Money(100000, Currency.AUD), account.cash_start_day)
        self.assertEqual(Money(0, Currency.AUD), account.cash_activity_day)
        self.assertEqual(Money(0, Currency.AUD), account.margin_used_liquidation)
        self.assertEqual(Money(20000, Currency.AUD), account.margin_used_maintenance)
        self.assertEqual(Decimal(0), account.margin_ratio)
        self.assertEqual('N', account.margin_call_status.value)
        self.assertEqual(UNIX_EPOCH, account.last_updated)

    def test_can_calculate_free_equity_when_negative(self):
        # Arrange
        event = AccountStateEvent(
            AccountId.py_from_string('FXCM-123456-SIMULATED'),
            Currency.AUD,
            Money(20000, Currency.AUD),
            Money(100000, Currency.AUD),
            Money(0, Currency.AUD),
            Money(10000, Currency.AUD),
            Money(20000, Currency.AUD),
            Decimal(0),
            ValidString('N'),
            GUID(uuid.uuid4()),
            UNIX_EPOCH)

        # Act
        account = Account(event)

        # Assert
        self.assertEqual(AccountId.py_from_string('FXCM-123456-SIMULATED'), account.id)
        self.assertEqual(Brokerage('FXCM'), account.broker)
        self.assertEqual(AccountNumber('123456'), account.account_number)
        self.assertEqual(Currency.AUD, account.currency)
        self.assertEqual(Money(0, Currency.AUD), account.free_equity)
        self.assertEqual(Money(100000, Currency.AUD), account.cash_start_day)
        self.assertEqual(Money(0, Currency.AUD), account.cash_activity_day)
        self.assertEqual(Money(10000, Currency.AUD), account.margin_used_liquidation)
        self.assertEqual(Money(20000, Currency.AUD), account.margin_used_maintenance)
        self.assertEqual(Decimal(0), account.margin_ratio)
        self.assertEqual('N', account.margin_call_status.value)
        self.assertEqual(UNIX_EPOCH, account.last_updated)