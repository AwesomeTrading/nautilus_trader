// -------------------------------------------------------------------------------------------------
//  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
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

//! String manipulation functionality.

use std::fmt::Display;

/// Placeholder used in `Debug` impls to redact secret fields.
pub const REDACTED: &str = "<redacted>";

/// Parsed semantic version with major, minor, and patch components.
///
/// Supports parsing `"X.Y.Z"` strings and lexicographic comparison
/// (major, then minor, then patch).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct SemVer {
    /// Major version number.
    pub major: u64,
    /// Minor version number.
    pub minor: u64,
    /// Patch version number.
    pub patch: u64,
}

impl SemVer {
    /// Parses a `"major.minor.patch"` string into a [`SemVer`].
    ///
    /// Missing components default to zero.
    pub fn parse(s: &str) -> anyhow::Result<Self> {
        let mut parts = s.split('.').map(str::parse::<u64>);
        let major = parts.next().unwrap_or(Ok(0))?;
        let minor = parts.next().unwrap_or(Ok(0))?;
        let patch = parts.next().unwrap_or(Ok(0))?;
        Ok(Self {
            major,
            minor,
            patch,
        })
    }
}

impl Display for SemVer {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}.{}.{}", self.major, self.minor, self.patch)
    }
}

/// Converts a string from any common case to `snake_case`.
///
/// Word boundaries are detected at:
/// - Non-alphanumeric characters (spaces, hyphens, underscores, colons, etc.)
/// - Transitions from lowercase or digit to uppercase (`camelCase` -> `camel_case`)
/// - Within consecutive uppercase letters, before the last if followed by lowercase
///   (`XMLParser` -> `xml_parser`)
#[must_use]
pub fn to_snake_case(s: &str) -> String {
    if s.is_ascii() {
        to_snake_case_ascii(s.as_bytes())
    } else {
        to_snake_case_unicode(s)
    }
}

fn to_snake_case_ascii(bytes: &[u8]) -> String {
    // Single pass over bytes. Mode tracks the case of the last cased character
    // within the current alphanumeric run, matching heck's word-boundary rules.
    const BOUNDARY: u8 = 0;
    const LOWER: u8 = 1;
    const UPPER: u8 = 2;

    let len = bytes.len();
    let mut result = String::with_capacity(len + len / 4);
    let mut first_word = true;
    let mut mode: u8 = BOUNDARY;
    let mut word_start = 0;
    let mut i = 0;

    while i < len {
        let b = bytes[i];

        if !b.is_ascii_alphanumeric() {
            if word_start < i {
                push_lower_ascii(&mut result, &bytes[word_start..i], &mut first_word);
            }
            word_start = i + 1;
            mode = BOUNDARY;
            i += 1;
            continue;
        }

        let next_mode = if b.is_ascii_lowercase() {
            LOWER
        } else if b.is_ascii_uppercase() {
            UPPER
        } else {
            mode
        };

        if i + 1 < len && bytes[i + 1].is_ascii_alphanumeric() {
            let next = bytes[i + 1];

            if next_mode == LOWER && next.is_ascii_uppercase() {
                push_lower_ascii(&mut result, &bytes[word_start..=i], &mut first_word);
                word_start = i + 1;
                mode = BOUNDARY;
            } else if mode == UPPER && b.is_ascii_uppercase() && next.is_ascii_lowercase() {
                if word_start < i {
                    push_lower_ascii(&mut result, &bytes[word_start..i], &mut first_word);
                }
                word_start = i;
                mode = BOUNDARY;
            } else {
                mode = next_mode;
            }
        }

        i += 1;
    }

    if word_start < len && bytes[word_start].is_ascii_alphanumeric() {
        push_lower_ascii(&mut result, &bytes[word_start..], &mut first_word);
    }

    result
}

fn push_lower_ascii(result: &mut String, word: &[u8], first_word: &mut bool) {
    if word.is_empty() {
        *first_word = false;
        return;
    }

    if !*first_word {
        result.push('_');
    }
    *first_word = false;

    for &b in word {
        result.push(char::from(b.to_ascii_lowercase()));
    }
}

fn to_snake_case_unicode(s: &str) -> String {
    #[derive(Clone, Copy, PartialEq)]
    enum Mode {
        Boundary,
        Lowercase,
        Uppercase,
    }

    let mut result = String::with_capacity(s.len() + s.len() / 4);
    let mut first_word = true;

    for word in s.split(|c: char| !c.is_alphanumeric()) {
        let mut char_indices = word.char_indices().peekable();
        let mut init = 0;
        let mut mode = Mode::Boundary;

        while let Some((i, c)) = char_indices.next() {
            if let Some(&(next_i, next)) = char_indices.peek() {
                let next_mode = if c.is_lowercase() {
                    Mode::Lowercase
                } else if c.is_uppercase() {
                    Mode::Uppercase
                } else {
                    mode
                };

                if next_mode == Mode::Lowercase && next.is_uppercase() {
                    push_lower_unicode(&mut result, &word[init..next_i], &mut first_word);
                    init = next_i;
                    mode = Mode::Boundary;
                } else if mode == Mode::Uppercase && c.is_uppercase() && next.is_lowercase() {
                    push_lower_unicode(&mut result, &word[init..i], &mut first_word);
                    init = i;
                    mode = Mode::Boundary;
                } else {
                    mode = next_mode;
                }
            } else {
                push_lower_unicode(&mut result, &word[init..], &mut first_word);
                break;
            }
        }
    }

    result
}

fn push_lower_unicode(result: &mut String, word: &str, first_word: &mut bool) {
    if word.is_empty() {
        *first_word = false;
        return;
    }

    if !*first_word {
        result.push('_');
    }
    *first_word = false;

    for c in word.chars() {
        for lc in c.to_lowercase() {
            result.push(lc);
        }
    }
}

/// Masks an API key by showing only the first and last 4 characters.
///
/// For keys 8 characters or shorter, returns asterisks only.
///
/// # Examples
///
/// ```
/// use nautilus_core::string::mask_api_key;
///
/// assert_eq!(mask_api_key("abcdefghijklmnop"), "abcd...mnop");
/// assert_eq!(mask_api_key("short"), "*****");
/// ```
#[must_use]
pub fn mask_api_key(key: &str) -> String {
    // Work with Unicode scalars to avoid panicking on multibyte characters.
    let chars: Vec<char> = key.chars().collect();
    let len = chars.len();

    if len <= 8 {
        return "*".repeat(len);
    }

    let first: String = chars[..4].iter().collect();
    let last: String = chars[len - 4..].iter().collect();

    format!("{first}...{last}")
}

#[cfg(test)]
mod tests {
    use rstest::rstest;

    use super::*;

    #[rstest]
    #[case("", "")]
    #[case("a", "*")]
    #[case("abc", "***")]
    #[case("abcdefgh", "********")]
    #[case("abcdefghi", "abcd...fghi")]
    #[case("abcdefghijklmnop", "abcd...mnop")]
    #[case("VeryLongAPIKey123456789", "Very...6789")]
    fn test_mask_api_key(#[case] input: &str, #[case] expected: &str) {
        assert_eq!(mask_api_key(input), expected);
    }

    #[rstest]
    #[case("CamelCase", "camel_case")]
    #[case("This is Human case.", "this_is_human_case")]
    #[case(
        "MixedUP CamelCase, with some Spaces",
        "mixed_up_camel_case_with_some_spaces"
    )]
    #[case(
        "mixed_up_ snake_case with some _spaces",
        "mixed_up_snake_case_with_some_spaces"
    )]
    #[case("kebab-case", "kebab_case")]
    #[case("SHOUTY_SNAKE_CASE", "shouty_snake_case")]
    #[case("snake_case", "snake_case")]
    #[case("XMLHttpRequest", "xml_http_request")]
    #[case("FIELD_NAME11", "field_name11")]
    #[case("99BOTTLES", "99bottles")]
    #[case("abc123def456", "abc123def456")]
    #[case("abc123DEF456", "abc123_def456")]
    #[case("abc123Def456", "abc123_def456")]
    #[case("abc123DEf456", "abc123_d_ef456")]
    #[case("ABC123def456", "abc123def456")]
    #[case("ABC123DEF456", "abc123def456")]
    #[case("ABC123Def456", "abc123_def456")]
    #[case("ABC123DEf456", "abc123d_ef456")]
    #[case("ABC123dEEf456FOO", "abc123d_e_ef456_foo")]
    #[case("abcDEF", "abc_def")]
    #[case("ABcDE", "a_bc_de")]
    #[case("", "")]
    #[case("A", "a")]
    #[case("AB", "ab")]
    #[case("PascalCase", "pascal_case")]
    #[case("camelCase", "camel_case")]
    #[case("getHTTPResponse", "get_http_response")]
    #[case("Level1", "level1")]
    #[case("OrderBookDelta", "order_book_delta")]
    #[case("IOError", "io_error")]
    #[case("SimpleHTTPServer", "simple_http_server")]
    #[case("version2Release", "version2_release")]
    #[case("ALLCAPS", "allcaps")]
    #[case("nautilus_model::data::bar::Bar", "nautilus_model_data_bar_bar")] // nautilus-import-ok
    fn test_to_snake_case(#[case] input: &str, #[case] expected: &str) {
        assert_eq!(to_snake_case(input), expected);
    }

    #[rstest]
    #[case("6.2.0", 6, 2, 0)]
    #[case("7.0.15", 7, 0, 15)]
    #[case("0.0.1", 0, 0, 1)]
    #[case("1", 1, 0, 0)]
    #[case("2.5", 2, 5, 0)]
    fn test_semver_parse(
        #[case] input: &str,
        #[case] major: u64,
        #[case] minor: u64,
        #[case] patch: u64,
    ) {
        let v = SemVer::parse(input).unwrap();
        assert_eq!(v.major, major);
        assert_eq!(v.minor, minor);
        assert_eq!(v.patch, patch);
    }

    #[rstest]
    fn test_semver_display() {
        let v = SemVer::parse("7.2.4").unwrap();
        assert_eq!(v.to_string(), "7.2.4");
    }

    #[rstest]
    fn test_semver_ordering() {
        let v620 = SemVer::parse("6.2.0").unwrap();
        let v700 = SemVer::parse("7.0.0").unwrap();
        let v621 = SemVer::parse("6.2.1").unwrap();
        let v630 = SemVer::parse("6.3.0").unwrap();

        assert!(v700 > v620);
        assert!(v621 > v620);
        assert!(v630 > v621);
        assert!(v700 >= v620);
        assert!(v620 >= v620);
    }

    #[rstest]
    fn test_semver_parse_invalid() {
        assert!(SemVer::parse("abc").is_err());
    }
}
