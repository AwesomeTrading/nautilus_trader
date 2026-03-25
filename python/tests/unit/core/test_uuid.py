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

from nautilus_trader.core import UUID4


def test_new_uuid4_produces_valid_format():
    uuid = UUID4()
    value = str(uuid)
    assert len(value) == 36
    assert len(value.replace("-", "")) == 32


def test_from_str():
    uuid = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c757")
    assert uuid.value == "2d89666b-1a1e-4a75-b193-4eb3b454c757"


def test_equality():
    uuid1 = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c757")
    uuid2 = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c757")
    uuid3 = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c758")

    assert uuid1 == uuid2
    assert uuid1 != uuid3


def test_hash():
    uuid1 = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c758")
    uuid2 = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c758")

    assert isinstance(hash(uuid1), int)
    assert hash(uuid1) == hash(uuid2)


def test_str_and_repr():
    uuid = UUID4.from_str("2d89666b-1a1e-4a75-b193-4eb3b454c758")

    assert str(uuid) == "2d89666b-1a1e-4a75-b193-4eb3b454c758"
    assert repr(uuid) == "UUID4(2d89666b-1a1e-4a75-b193-4eb3b454c758)"


def test_pickle_round_trip():
    uuid = UUID4()
    pickled = pickle.dumps(uuid)
    unpickled = pickle.loads(pickled)  # noqa: S301

    assert unpickled == uuid
