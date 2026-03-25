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

import pickle

import pytest

from nautilus_trader.model import AccountId
from nautilus_trader.model import ExecAlgorithmId
from nautilus_trader.model import InstrumentId
from nautilus_trader.model import Symbol
from nautilus_trader.model import TraderId
from nautilus_trader.model import Venue


def test_trader_id_equality_and_value():
    tid1 = TraderId("TESTER-000")
    tid2 = TraderId("TESTER-001")

    assert tid1 == tid1
    assert tid1 != tid2
    assert tid1.value == "TESTER-000"


def test_account_id_equality_and_value():
    aid1 = AccountId("SIM-02851908")
    aid2 = AccountId("SIM-09999999")

    assert aid1 == aid1
    assert aid1 != aid2
    assert aid1.value == "SIM-02851908"
    assert aid1 == AccountId("SIM-02851908")


def test_symbol_equality():
    s1 = Symbol("AUD/USD")
    s2 = Symbol("ETH/USD")
    s3 = Symbol("AUD/USD")

    assert s1 == s1
    assert s1 != s2
    assert s1 == s3


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("AUDUSD", False),
        ("AUD/USD", False),
        ("CL.FUT", True),
        ("LO.OPT", True),
        ("ES.c.0", True),
    ],
)
def test_symbol_is_composite(value, expected):
    assert Symbol(value).is_composite == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("AUDUSD", "AUDUSD"),
        ("AUD/USD", "AUD/USD"),
        ("CL.FUT", "CL"),
        ("LO.OPT", "LO"),
        ("ES.c.0", "ES"),
    ],
)
def test_symbol_root(value, expected):
    assert Symbol(value).root == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("AUDUSD", "AUDUSD"),
        ("AUD/USD", "AUD/USD"),
        ("CL.FUT", "CL*"),
        ("LO.OPT", "LO*"),
        ("ES.c.0", "ES*"),
    ],
)
def test_symbol_topic(value, expected):
    assert Symbol(value).topic == expected


def test_symbol_str_and_repr():
    symbol = Symbol("AUD/USD")
    assert str(symbol) == "AUD/USD"
    assert repr(symbol) == "Symbol('AUD/USD')"


def test_symbol_pickle():
    symbol = Symbol("AUD/USD")
    pickled = pickle.dumps(symbol)
    unpickled = pickle.loads(pickled)  # noqa: S301
    assert unpickled == symbol


def test_venue_equality():
    v1 = Venue("SIM")
    v2 = Venue("IDEALPRO")
    v3 = Venue("SIM")

    assert v1 == v1
    assert v1 != v2
    assert v1 == v3


def test_venue_str_and_repr():
    venue = Venue("NYMEX")
    assert str(venue) == "NYMEX"
    assert repr(venue) == "Venue('NYMEX')"


def test_venue_pickle():
    venue = Venue("NYMEX")
    pickled = pickle.dumps(venue)
    unpickled = pickle.loads(pickled)  # noqa: S301
    assert unpickled == venue


def test_instrument_id_equality():
    id1 = InstrumentId(Symbol("AUD/USD"), Venue("SIM"))
    id2 = InstrumentId(Symbol("AUD/USD"), Venue("IDEALPRO"))
    id3 = InstrumentId(Symbol("GBP/USD"), Venue("SIM"))

    assert id1 == id1
    assert id1 != id2
    assert id1 != id3


def test_instrument_id_str_and_repr():
    iid = InstrumentId(Symbol("AUD/USD"), Venue("SIM"))
    assert str(iid) == "AUD/USD.SIM"
    assert repr(iid) == "InstrumentId('AUD/USD.SIM')"


def test_instrument_id_from_str():
    iid = InstrumentId.from_str("AUD/USD.SIM")
    assert str(iid.symbol) == "AUD/USD"
    assert str(iid.venue) == "SIM"


def test_instrument_id_from_str_with_utf8():
    iid = InstrumentId.from_str("TËST-PÉRP.BINANCE")
    assert str(iid.symbol) == "TËST-PÉRP"
    assert str(iid.venue) == "BINANCE"


@pytest.mark.parametrize(
    ("value", "expected_err"),
    [
        (
            "BTCUSDT",
            "Error parsing `InstrumentId` from 'BTCUSDT': "
            "missing '.' separator between symbol and venue components",
        ),
        (".USDT", "invalid string for 'value', was empty"),
        ("BTC.", "invalid string for 'value', was empty"),
    ],
)
def test_instrument_id_from_str_invalid(value, expected_err):
    with pytest.raises(ValueError, match=expected_err.replace("(", r"\(").replace(")", r"\)")):
        InstrumentId.from_str(value)


def test_instrument_id_pickle():
    iid = InstrumentId(Symbol("AUD/USD"), Venue("SIM"))
    pickled = pickle.dumps(iid)
    unpickled = pickle.loads(pickled)  # noqa: S301
    assert unpickled == iid


def test_exec_algorithm_id():
    ea1 = ExecAlgorithmId("VWAP")
    ea2 = ExecAlgorithmId("TWAP")

    assert ea1 == ea1
    assert ea1 != ea2
    assert isinstance(hash(ea1), int)
    assert str(ea1) == "VWAP"
    assert repr(ea1) == "ExecAlgorithmId('VWAP')"
