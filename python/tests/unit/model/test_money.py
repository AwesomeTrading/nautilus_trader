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

import math
import pickle
from decimal import Decimal

import pytest

from nautilus_trader.model import Currency
from nautilus_trader.model import Money


USD = Currency.from_str("USD")
AUD = Currency.from_str("AUD")
USDT = Currency.from_str("USDT")


def test_nan_raises():
    with pytest.raises(ValueError, match="NaN"):
        Money(math.nan, currency=USD)


def test_none_value_raises():
    with pytest.raises(TypeError):
        Money(None, currency=USD)


def test_none_currency_raises():
    with pytest.raises(TypeError):
        Money(1.0, None)


def test_value_exceeding_positive_limit_raises():
    with pytest.raises(ValueError, match="not in range"):
        Money(1e18, currency=USD)


def test_value_exceeding_negative_limit_raises():
    with pytest.raises(ValueError, match="not in range"):
        Money(-1e18, currency=USD)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, Money(0, USD)),
        (1, Money(1, USD)),
        (-1, Money(-1, USD)),
    ],
)
def test_construction(value, expected):
    assert Money(value, USD) == expected


def test_as_double():
    money = Money(1.0, USD)
    assert money.as_double() == 1.0
    assert str(money) == "1.00 USD"


def test_rounds_to_currency_precision():
    r1 = Money(1000.333, USD)
    r2 = Money(5005.556666, USD)
    assert str(r1) == "1000.33 USD"
    assert str(r2) == "5005.56 USD"
    assert r1.to_formatted_str() == "1_000.33 USD"
    assert r2.to_formatted_str() == "5_005.56 USD"


def test_equality_different_currencies_raises():
    with pytest.raises(ValueError, match="Cannot compare Money with different currencies"):
        assert Money(1, USD) != Money(1, AUD)


def test_equality():
    m1 = Money(1, USD)
    m2 = Money(1, USD)
    m3 = Money(2, USD)
    assert m1 == m2
    assert m1 != m3


def test_hash():
    m = Money(0, USD)
    assert isinstance(hash(m), int)
    assert hash(m) == hash(m)


def test_str():
    assert str(Money(0, USD)) == "0.00 USD"
    assert str(Money(1, USD)) == "1.00 USD"
    assert str(Money(1_000_000, USD)) == "1000000.00 USD"
    assert Money(1_000_000, USD).to_formatted_str() == "1_000_000.00 USD"


def test_repr():
    assert repr(Money(1.00, USD)) == "Money(1.00, USD)"


def test_from_raw():
    assert Money.from_raw(0, USDT) == Money(0, USDT)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1.00 USDT", Money(1.00, USDT)),
        ("1.00 USD", Money(1.00, USD)),
        ("1.001 AUD", Money(1.00, AUD)),
    ],
)
def test_from_str(value, expected):
    result = Money.from_str(value)
    assert result == expected


def test_from_str_malformed_raises():
    with pytest.raises(ValueError, match="invalid input format"):
        Money.from_str("@")


def test_from_decimal():
    money = Money.from_decimal(Decimal("100.50"), USD)
    assert money == Money(100.50, USD)
    assert str(money) == "100.50 USD"


def test_from_decimal_zero():
    money = Money.from_decimal(Decimal(0), USD)
    assert money.as_double() == 0
    assert str(money) == "0.00 USD"


def test_from_decimal_negative():
    money = Money.from_decimal(Decimal("-50.25"), USD)
    assert money.as_double() == -50.25
    assert str(money) == "-50.25 USD"


def test_from_decimal_rounds():
    money = Money.from_decimal(Decimal("100.123"), USD)
    assert str(money) == "100.12 USD"


def test_from_decimal_high_precision():
    money = Money.from_decimal(Decimal("100.12345678"), USDT)
    assert str(money) == "100.12345678 USDT"


def test_pickle():
    money = Money(1, USD)
    pickled = pickle.dumps(money)
    unpickled = pickle.loads(pickled)  # noqa: S301
    assert unpickled == money


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Money(1.00, USD), Money(2.00, USD), Money, Money(3.00, USD)),
        (Money(0.00, USD), Money(0.00, USD), Money, Money(0.00, USD)),
        (Money(-1.00, USD), Money(1.00, USD), Money, Money(0.00, USD)),
        (Money(1.00, USD), 2, Decimal, Decimal("3.00")),
        (2, Money(1.00, USD), Decimal, Decimal("3.00")),
        (Money(1.00, USD), 2.5, float, 3.5),
        (2.5, Money(1.00, USD), float, 3.5),
    ],
)
def test_addition(v1, v2, expected_type, expected):
    result = v1 + v2
    assert isinstance(result, expected_type)
    assert result == expected


def test_addition_different_currencies_raises():
    with pytest.raises(ValueError, match="Currency mismatch"):
        Money(1.00, USD) + Money(1.00, AUD)


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Money(3.00, USD), Money(2.00, USD), Money, Money(1.00, USD)),
        (Money(1.00, USD), Money(1.00, USD), Money, Money(0.00, USD)),
        (Money(3.00, USD), 2, Decimal, Decimal("1.00")),
        (3, Money(2.00, USD), Decimal, Decimal("1.00")),
        (Money(3.00, USD), 2.5, float, 0.5),
        (3.5, Money(2.00, USD), float, 1.5),
    ],
)
def test_subtraction(v1, v2, expected_type, expected):
    result = v1 - v2
    assert isinstance(result, expected_type)
    assert result == expected


def test_subtraction_different_currencies_raises():
    with pytest.raises(ValueError, match="Currency mismatch"):
        Money(1.00, USD) - Money(1.00, AUD)


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Money(2.00, USD), 3, Decimal, Decimal("6.00")),
        (3, Money(2.00, USD), Decimal, Decimal("6.00")),
        (Money(2.00, USD), 1.5, float, 3.0),
        (1.5, Money(2.00, USD), float, 3.0),
        (Money(2.00, USD), Money(3.00, USD), Decimal, Decimal("6.00")),
    ],
)
def test_multiplication(v1, v2, expected_type, expected):
    result = v1 * v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Money(6.00, USD), 3, Decimal, Decimal("2.00")),
        (6, Money(3.00, USD), Decimal, Decimal("2.00")),
        (Money(6.00, USD), 2.0, float, 3.0),
        (6.0, Money(2.00, USD), float, 3.0),
        (Money(6.00, USD), Money(3.00, USD), Decimal, Decimal("2.00")),
    ],
)
def test_division(v1, v2, expected_type, expected):
    result = v1 / v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Money(7.00, USD), 3, Decimal, Decimal(2)),
        (7, Money(3.00, USD), Decimal, Decimal(2)),
        (Money(7.00, USD), 3.0, float, 2.0),
        (7.0, Money(3.00, USD), float, 2.0),
        (Money(7.00, USD), Money(3.00, USD), Decimal, Decimal(2)),
    ],
)
def test_floor_division(v1, v2, expected_type, expected):
    result = v1 // v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Money(7.00, USD), 3, Decimal, Decimal("1.00")),
        (Money(7.00, USD), 3.0, float, 1.0),
        (Money(7.00, USD), Money(3.00, USD), Decimal, Decimal("1.00")),
    ],
)
def test_mod(v1, v2, expected_type, expected):
    result = v1 % v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Money(1.00, USD), Money(-1.00, USD)),
        (Money(-1.00, USD), Money(1.00, USD)),
        (Money(0.00, USD), Money(0.00, USD)),
    ],
)
def test_neg(value, expected):
    result = -value
    assert isinstance(result, Money)
    assert result == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Money(1.00, USD), Money(1.00, USD)),
        (Money(-1.00, USD), Money(1.00, USD)),
        (Money(0.00, USD), Money(0.00, USD)),
    ],
)
def test_abs(value, expected):
    result = abs(value)
    assert isinstance(result, Money)
    assert result == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Money(50.25, USD), 50),
        (Money(-50.25, USD), -50),
        (Money(0.00, USD), 0),
    ],
)
def test_int(value, expected):
    assert int(value) == expected
