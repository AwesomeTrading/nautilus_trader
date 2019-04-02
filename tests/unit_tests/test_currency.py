#!/usr/bin/env python3
# -------------------------------------------------------------------------------------------------
# <copyright file="test_currency.py" company="Invariance Pte">
#  Copyright (C) 2018-2019 Invariance Pte. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE.md file.
#  http://www.invariance.com
# </copyright>
# -------------------------------------------------------------------------------------------------

import unittest

from inv_trader.enums.currency import Currency
from inv_trader.enums.quote_type import QuoteType
from inv_trader.model.currency import CurrencyCalculator


class CurrencyConverterTests(unittest.TestCase):

    def test_can_calculate_exchange_rate(self):
        # Arrange
        converter = CurrencyCalculator()
        bid_rates = {'AUDUSD': 0.80000}
        ask_rates = {'AUDUSD': 0.80010}

        # Act
        result = converter.exchange_rate(
            Currency.AUD,
            Currency.USD,
            QuoteType.BID,
            bid_rates,
            ask_rates)

        # Assert
        self.assertEqual(0.800000011920929, result)

    def test_can_calculate_exchange_rate_for_inverse(self):
        # Arrange
        converter = CurrencyCalculator()
        bid_rates = {'USDJPY': 110.100}
        ask_rates = {'USDJPY': 110.130}

        # Act
        result = converter.exchange_rate(
            Currency.JPY,
            Currency.USD,
            QuoteType.BID,
            bid_rates,
            ask_rates)

        # Assert
        self.assertEqual(0.009082651697099209, result)

    def test_can_calculate_exchange_rate_by_inference(self):
        # Arrange
        converter = CurrencyCalculator()
        bid_rates = {
            'USDJPY': 110.100,
            'AUDUSD': 0.80000
        }
        ask_rates = {
            'USDJPY': 110.130,
            'AUDUSD': 0.80010}

        # Act
        result = converter.exchange_rate(
            Currency.JPY,
            Currency.AUD,
            QuoteType.BID,
            bid_rates,
            ask_rates)

        # Assert
        self.assertEqual(0.0, result)

    def test_can_calculate_exchange_rate_for_mid_quote_type(self):
        # Arrange
        converter = CurrencyCalculator()
        bid_rates = {'USDJPY': 110.100}
        ask_rates = {'USDJPY': 110.130}

        # Act
        result = converter.exchange_rate(
            Currency.JPY,
            Currency.USD,
            QuoteType.MID,
            bid_rates,
            ask_rates)

        # Assert
        self.assertEqual(0.00908141490072012, result)

    def test_can_calculate_exchange_rate_for_mid_quote_type2(self):
        # Arrange
        converter = CurrencyCalculator()
        bid_rates = {'USDJPY': 110.100}
        ask_rates = {'USDJPY': 110.130}

        # Act
        result = converter.exchange_rate(
            Currency.USD,
            Currency.JPY,
            QuoteType.MID,
            bid_rates,
            ask_rates)

        # Assert
        self.assertEqual(110.11499786376953, result)
