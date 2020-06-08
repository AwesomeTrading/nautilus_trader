# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2020 Nautech Systems Pty Ltd. All rights reserved.
#  The use of this source code is governed by the license as found in the LICENSE file.
#  https://nautechsystems.io
# -------------------------------------------------------------------------------------------------

import unittest

from nautilus_trader.model.objects import Price
from nautilus_trader.serialization.common import *
from nautilus_trader.serialization.serializers import *
from tests.test_kit.stubs import UNIX_EPOCH


class SerializationFunctionTests(unittest.TestCase):

    def test_can_convert_price_to_string_from_none(self):
        # Arrange
        # Act
        result = convert_price_to_string(None)

        # Assert
        self.assertEqual('None', result)

    def test_can_convert_price_to_string_from_decimal(self):
        # Arrange
        # Act
        result = convert_price_to_string(Price(1.00000, 5))

        # Assert
        self.assertEqual('1.00000', result)

    def test_can_convert_string_to_price_from_none(self):
        # Arrange
        # Act
        result = convert_string_to_price('None')

        # Assert
        self.assertEqual(None, result)

    def test_can_convert_string_to_price_from_decimal(self):
        # Arrange
        # Act
        result = convert_string_to_price('1.00000')

        # Assert
        self.assertEqual(Price(1.00000, 5), result)

    def test_can_convert_datetime_to_string_from_none(self):
        # Arrange
        # Act
        result = convert_datetime_to_string(None)

        # Assert
        self.assertEqual('None', result)

    def test_can_convert_datetime_to_string(self):
        # Arrange
        # Act
        result = convert_datetime_to_string(UNIX_EPOCH)

        # Assert
        self.assertEqual('1970-01-01T00:00:00.000Z', result)

    def test_can_convert_string_to_time_from_datetime(self):
        # Arrange
        # Act
        result = convert_string_to_datetime('1970-01-01T00:00:00.000Z')

        # Assert
        self.assertEqual(UNIX_EPOCH, result)

    def test_can_convert_string_to_time_from_none(self):
        # Arrange
        # Act
        result = convert_string_to_datetime('None')

        # Assert
        self.assertEqual(None, result)