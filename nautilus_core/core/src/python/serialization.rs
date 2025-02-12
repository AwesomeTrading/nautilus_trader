// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2025 Nautech Systems Pty Ltd. All rights reserved.
//  https://nautechsystems.io
//
//  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
//  You may not use this file except in compliance with the License.
//  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
//
//  Unless required by applicable law or agreed to in writing, software
//  distributed under the License is distributed on an "AS IS" BASIS,
//  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//  See the License for the specific language governing permissions and
//  limitations under the License.
// -------------------------------------------------------------------------------------------------

use pyo3::{prelude::*, types::PyDict};
use serde::de::DeserializeOwned;

pub fn from_dict_pyo3<T>(py: Python<'_>, values: Py<PyDict>) -> Result<T, PyErr>
where
    T: DeserializeOwned,
{
    // Extract to JSON bytes
    use crate::python::to_pyvalue_err;
    let json_bytes: Vec<u8> = PyModule::import_bound(py, "msgspec.json")?
        .call_method("encode", (values,), None)?
        .extract()?;

    // Deserialize to object
    let instance = serde_json::from_slice(&json_bytes).map_err(to_pyvalue_err)?;
    Ok(instance)
}
