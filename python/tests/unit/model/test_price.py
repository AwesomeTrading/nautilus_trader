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

from nautilus_trader.model import FIXED_PRECISION
from nautilus_trader.model import Price


def test_nan_raises():
    with pytest.raises(ValueError, match="NaN"):
        Price(math.nan, precision=0)


def test_none_raises():
    with pytest.raises(TypeError):
        Price(None, precision=0)


def test_negative_precision_raises():
    with pytest.raises(OverflowError):
        Price(1.0, precision=-1)


def test_precision_over_max_raises():
    with pytest.raises(ValueError, match="precision"):
        Price(1.0, precision=FIXED_PRECISION + 1)


def test_value_exceeding_positive_limit_raises():
    with pytest.raises(ValueError, match="not in range"):
        Price(1e18, precision=0)


def test_value_exceeding_negative_limit_raises():
    with pytest.raises(ValueError, match="not in range"):
        Price(-1e18, precision=0)


def test_from_int():
    result = Price(1, precision=1)
    assert result.raw == 10**FIXED_PRECISION
    assert str(result) == "1.0"


def test_from_float():
    result = Price(1.12300, precision=5)
    expected_raw = int(1.123 * (10**FIXED_PRECISION))
    assert result.raw == expected_raw
    assert str(result) == "1.12300"


def test_from_decimal():
    result = Price(Decimal("1.23"), precision=1)
    assert str(result) == "1.2"


def test_from_str():
    result = Price.from_str("1.23")
    assert str(result) == "1.23"


def test_from_int_method():
    price = Price.from_int(100)
    assert str(price) == "100"
    assert price.precision == 0


@pytest.mark.parametrize(
    ("value", "string", "precision"),
    [
        ("100.11", "100.11", 2),
        ("1E7", "10000000", 0),
        ("1E-7", "0.0000001", 7),
        ("1e-2", "0.01", 2),
    ],
)
def test_from_str_various(value, string, precision):
    price = Price.from_str(value)
    assert str(price) == string
    assert price.precision == precision


def test_from_raw():
    raw = 1000 * (10**FIXED_PRECISION)
    price = Price.from_raw(raw, 3)
    assert str(price) == "1000.000"
    assert price.precision == 3
    assert price == Price(1000, 3)


def test_from_decimal_infers_precision():
    price = Price.from_decimal(Decimal("123.456"))
    assert price.precision == 3
    assert str(price) == "123.456"


def test_from_decimal_integer():
    price = Price.from_decimal(Decimal(100))
    assert price.precision == 0
    assert str(price) == "100"


def test_from_decimal_high_precision():
    price = Price.from_decimal(Decimal("1.23456789"))
    assert price.precision == 8
    assert str(price) == "1.23456789"


def test_from_decimal_negative():
    price = Price.from_decimal(Decimal("-99.95"))
    assert price.precision == 2
    assert str(price) == "-99.95"


def test_from_decimal_trailing_zeros():
    price = Price.from_decimal(Decimal("1.230"))
    assert price.precision == 3
    assert str(price) == "1.230"


def test_from_decimal_dp():
    price = Price.from_decimal_dp(Decimal("123.456789"), 2)
    assert price.precision == 2
    assert str(price) == "123.46"


def test_from_decimal_dp_bankers_rounding():
    p1 = Price.from_decimal_dp(Decimal("1.005"), 2)
    p2 = Price.from_decimal_dp(Decimal("1.015"), 2)
    assert str(p1) == "1.00"
    assert str(p2) == "1.02"


def test_from_decimal_dp_precision_limits():
    price = Price.from_decimal_dp(Decimal("1.0"), FIXED_PRECISION)
    assert price.precision == FIXED_PRECISION

    with pytest.raises(ValueError, match="precision"):
        Price.from_decimal_dp(Decimal("1.0"), 19)


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        (0.0, 0, Price(0, precision=0)),
        (1.0, 0, Price(1, precision=0)),
        (-1.0, 0, Price(-1, precision=0)),
        (1.123, 3, Price(1.123, precision=3)),
        (-1.123, 3, Price(-1.123, precision=3)),
        (1.155, 2, Price(1.16, precision=2)),
    ],
)
def test_various_precisions(value, precision, expected):
    result = Price(value, precision)
    assert result == expected
    assert result.precision == precision


def test_equality():
    p1 = Price(1.0, precision=1)
    p2 = Price(1.5, precision=1)
    assert p1 == p1
    assert p1 != p2
    assert p2 > p1


@pytest.mark.parametrize(
    ("v1", "v2", "expected"),
    [
        (0, -0, True),
        (-1, -1, True),
        (1, 1, True),
        (1.1, 1.1, True),
        (0, 1, False),
        (-1, 0, False),
        (1.1, 1.12, False),
    ],
)
def test_equality_parametrized(v1, v2, expected):
    assert (Price(v1, 2) == Price(v2, 2)) == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected"),
    [
        (0, -0, True),
        (1, 1, True),
        (0, 1, False),
        (-1, 0, False),
    ],
)
def test_equality_with_int(v1, v2, expected):
    assert (Price(v1, 0) == v2) == expected
    assert (v2 == Price(v1, 0)) == expected


@pytest.mark.parametrize(
    ("v1", "v2", "gt", "ge", "le", "lt"),
    [
        (0, 0, False, True, True, False),
        (1, 0, True, True, False, False),
        (-1, 0, False, False, True, True),
    ],
)
def test_comparisons(v1, v2, gt, ge, le, lt):
    p1, p2 = Price(v1, precision=0), Price(v2, precision=0)
    assert (p1 > p2) == gt
    assert (p1 >= p2) == ge
    assert (p1 <= p2) == le
    assert (p1 < p2) == lt


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Price(1, 0), Price(-1, 0)),
        (Price(-1, 0), Price(1, 0)),
        (Price(0, 0), Price(0, 0)),
        (Price(-1.5, 1), Price(1.5, 1)),
    ],
)
def test_neg(value, expected):
    result = -value
    assert isinstance(result, Price)
    assert result == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (Price(-0, 0), Price(0, 0)),
        (Price(0, 0), Price(0, 0)),
        (Price(1, 0), Price(1, 0)),
        (Price(-1, 0), Price(1, 0)),
        (Price(-1.1, 1), Price(1.1, 1)),
    ],
)
def test_abs(value, expected):
    result = abs(value)
    assert isinstance(result, Price)
    assert result == expected


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        (Price(2.15, 2), 0, Decimal(2)),
        (Price(2.15, 2), 1, Decimal("2.2")),
        (Price(2.255, 3), 2, Decimal("2.26")),
    ],
)
def test_round(value, precision, expected):
    assert round(value, precision) == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Price(0, 0), Price(0, 0), Price, Price(0, 0)),
        (Price(0, 0), Price(1.1, 1), Price, Price(1.1, 1)),
        (Price(1, 0), Price(1.1, 1), Price, Price(2.1, 1)),
        (Price(0, 0), 0, Decimal, 0),
        (Price(0, 0), 1, Decimal, 1),
        (0, Price(0, 0), Decimal, 0),
        (1, Price(0, 0), Decimal, 1),
        (Price(0, 0), 0.1, float, 0.1),
        (Price(0, 0), 1.1, float, 1.1),
        (1.1, Price(0, 0), float, 1.1),
        (Price(1, 0), Decimal("1.1"), Decimal, Decimal("2.1")),
    ],
)
def test_addition(v1, v2, expected_type, expected):
    result = v1 + v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Price(0, 0), Price(0, 0), Price, Price(0, 0)),
        (Price(0, 0), Price(1.1, 1), Price, Price(-1.1, 1)),
        (Price(1, 0), Price(1.1, 1), Price, Price(-0.1, 1)),
        (Price(0, 0), 0, Decimal, 0),
        (Price(0, 0), 1, Decimal, -1),
        (0, Price(0, 0), Decimal, 0),
        (1, Price(1, 0), Decimal, 0),
        (Price(0, 0), 0.1, float, -0.1),
        (Price(0, 0), 1.1, float, -1.1),
        (Price(1, 0), Decimal("1.1"), Decimal, Decimal("-0.1")),
    ],
)
def test_subtraction(v1, v2, expected_type, expected):
    result = v1 - v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (Price(0, 0), 0, Decimal, 0),
        (Price(1, 0), 1, Decimal, 1),
        (1, Price(1, 0), Decimal, 1),
        (2, Price(3, 0), Decimal, 6),
        (Price(2, 0), 1.0, float, 2),
        (1.1, Price(2, 0), float, 2.2),
        (Price(1.1, 1), Price(1.1, 1), Decimal, Decimal("1.21")),
        (Price(1.1, 1), Decimal("1.1"), Decimal, Decimal("1.21")),
    ],
)
def test_multiplication(v1, v2, expected_type, expected):
    result = v1 * v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (1, Price(1, 0), Decimal, 1),
        (Price(0, 0), 1, Decimal, 0),
        (Price(1, 0), 2, Decimal, Decimal("0.5")),
        (2, Price(1, 0), Decimal, Decimal("2.0")),
        (Price(2, 0), 1.1, float, 1.8181818181818181),
        (1.1, Price(2, 0), float, 1.1 / 2),
        (Price(1.1, 1), Price(1.2, 1), Decimal, Decimal("0.9166666666666666666666666667")),
        (Price(1.1, 1), Decimal("1.2"), Decimal, Decimal("0.9166666666666666666666666667")),
    ],
)
def test_division(v1, v2, expected_type, expected):
    result = v1 / v2
    assert isinstance(result, expected_type)
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (1, Price(1, 0), Decimal, 1),
        (Price(0, 0), 1, Decimal, 0),
        (Price(1, 0), 2, Decimal, Decimal(0)),
        (2, Price(1, 0), Decimal, Decimal(2)),
        (2.1, Price(1.1, 1), float, 1),
        (Price(2.1, 1), 1.1, float, 1),
        (Price(1.1, 1), Price(1.2, 1), Decimal, Decimal(0)),
        (Price(1.1, 1), Decimal("1.2"), Decimal, Decimal(0)),
    ],
)
def test_floor_division(v1, v2, expected_type, expected):
    result = v1 // v2
    assert type(result) is expected_type
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected_type", "expected"),
    [
        (1, Price(1, 0), Decimal, 0),
        (Price(100, 0), 10, Decimal, 0),
        (Price(23, 0), 2, Decimal, 1),
        (2.1, Price(1.1, 1), float, 1.0),
        (Price(2.1, 1), 1.1, float, 1.0),
        (Price(1.1, 1), Price(0.2, 1), Decimal, Decimal("0.1")),
    ],
)
def test_mod(v1, v2, expected_type, expected):
    result = v1 % v2
    assert type(result) is expected_type
    assert result == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected"),
    [
        (Price(1, 0), Price(2, 0), Price(2, 0)),
        (Price(1, 0), 2, 2),
        (Price(1, 0), Decimal(2), Decimal(2)),
    ],
)
def test_max(v1, v2, expected):
    assert max(v1, v2) == expected


@pytest.mark.parametrize(
    ("v1", "v2", "expected"),
    [
        (Price(1, 0), Price(2, 0), Price(1, 0)),
        (Price(1, 0), 2, Price(1, 0)),
        (Price(2, 0), Decimal(1), Decimal(1)),
    ],
)
def test_min(v1, v2, expected):
    assert min(v1, v2) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", 1), ("1.1", 1)],
)
def test_int(value, expected):
    assert int(Price.from_str(value)) == expected


def test_hash():
    p1 = Price(1.1, 1)
    p2 = Price(1.1, 1)
    assert isinstance(hash(p1), int)
    assert hash(p1) == hash(p2)


@pytest.mark.parametrize(
    ("value", "precision", "expected"),
    [
        (0, 0, "0"),
        (-0, 0, "0"),
        (-1, 0, "-1"),
        (1, 0, "1"),
        (1.1, 1, "1.1"),
        (-1.1, 1, "-1.1"),
    ],
)
def test_str(value, precision, expected):
    assert str(Price(value, precision=precision)) == expected


def test_repr():
    assert repr(Price(1.1, 1)) == "Price(1.1)"
    assert repr(Price(1.00000, 5)) == "Price(1.00000)"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, 0), (-0, 0), (-1, -1), (1, 1), (1.1, 1.1), (-1.1, -1.1)],
)
def test_as_double(value, expected):
    assert Price(value, 1).as_double() == expected


def test_pickle():
    price = Price(1.2000, 2)
    pickled = pickle.dumps(price)
    assert pickle.loads(pickled) == price  # noqa: S301
