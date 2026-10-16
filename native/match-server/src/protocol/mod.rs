//! CODOL 3.3.3.3 wire protocol, ported from this project's Python implementation.
//! Source attribution: src/match_server/NOTICE.md. No legacy engine dependency.
//! SPDX-License-Identifier: AGPL-3.0-or-later

use std::collections::BTreeMap;

pub type Fields = BTreeMap<usize, u64>;
pub type UserCmd = BTreeMap<String, u32>;
pub type Result<T> = std::result::Result<T, String>;
mod p224;

pub mod transport;
pub use transport::{nat_reply, Association};
pub mod input;
pub mod wire;
pub mod snapshot;
pub use snapshot::{Inventory, encode_snapshot};
pub mod connection;
pub use connection::Connection;
