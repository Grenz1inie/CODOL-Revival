//! P-224 ECDH through Windows CNG, without an additional Cargo dependency.
//! CNG ECCPUBLICBLOB coordinates are big endian; TRUNCATE returns little endian.
//! https://learn.microsoft.com/windows/win32/seccng/cng-named-elliptic-curves
//! https://learn.microsoft.com/windows/win32/api/bcrypt/nf-bcrypt-bcryptderivekey
//! SPDX-License-Identifier: AGPL-3.0-or-later

use super::Result;

#[cfg(windows)]
mod cng {
    use super::Result;
    use std::{ffi::c_void, ptr::null_mut};
    type Handle = *mut c_void;

    #[link(name = "bcrypt")]
    unsafe extern "system" {
        fn BCryptOpenAlgorithmProvider(handle: *mut Handle, name: *const u16, provider: *const u16, flags: u32) -> i32;
        fn BCryptSetProperty(handle: Handle, name: *const u16, input: *const u8, size: u32, flags: u32) -> i32;
        fn BCryptGenerateKeyPair(algorithm: Handle, key: *mut Handle, bits: u32, flags: u32) -> i32;
        fn BCryptFinalizeKeyPair(key: Handle, flags: u32) -> i32;
        fn BCryptExportKey(key: Handle, export: Handle, kind: *const u16, output: *mut u8, size: u32, used: *mut u32, flags: u32) -> i32;
        fn BCryptImportKeyPair(algorithm: Handle, import: Handle, kind: *const u16, key: *mut Handle, input: *const u8, size: u32, flags: u32) -> i32;
        fn BCryptSecretAgreement(private: Handle, public: Handle, secret: *mut Handle, flags: u32) -> i32;
        fn BCryptDeriveKey(secret: Handle, kdf: *const u16, params: Handle, output: *mut u8, size: u32, used: *mut u32, flags: u32) -> i32;
        fn BCryptDestroyKey(key: Handle) -> i32;
        fn BCryptDestroySecret(secret: Handle) -> i32;
        fn BCryptCloseAlgorithmProvider(algorithm: Handle, flags: u32) -> i32;
    }

    fn wide(value: &str) -> Vec<u16> { value.encode_utf16().chain([0]).collect() }
    fn check(status: i32) -> Result<()> {
        if status < 0 { Err(format!("P-224 CNG failed: 0x{:08x}",status as u32)) } else { Ok(()) }
    }
    struct Algorithm(Handle);
    struct Key(Handle);
    struct Secret(Handle);
    impl Drop for Algorithm { fn drop(&mut self) { if !self.0.is_null() { unsafe { BCryptCloseAlgorithmProvider(self.0,0); } } } }
    impl Drop for Key { fn drop(&mut self) { if !self.0.is_null() { unsafe { BCryptDestroyKey(self.0); } } } }
    impl Drop for Secret { fn drop(&mut self) { if !self.0.is_null() { unsafe { BCryptDestroySecret(self.0); } } } }

    pub struct KeyPair { key: Key, algorithm: Algorithm }
    // Owned CNG handles have no thread affinity. Association owns them exclusively.
    unsafe impl Send for KeyPair {}

    impl KeyPair {
        pub fn generate() -> Result<Self> {
            let mut algorithm = Algorithm(null_mut());
            let mut key = Key(null_mut());
            let curve = wide("nistP224");
            // All pointers refer to live buffers/owned handles for each synchronous call.
            unsafe {
                check(BCryptOpenAlgorithmProvider(&mut algorithm.0,wide("ECDH").as_ptr(),std::ptr::null(),0))?;
                check(BCryptSetProperty(algorithm.0,wide("ECCCurveName").as_ptr(),curve.as_ptr().cast(),(curve.len()*2) as u32,0))?;
                check(BCryptGenerateKeyPair(algorithm.0,&mut key.0,224,0))?;
                check(BCryptFinalizeKeyPair(key.0,0))?;
            }
            Ok(Self { key,algorithm })
        }

        pub fn public(&self) -> Result<[u8;56]> {
            let mut blob = [0;64];
            let mut used = 0;
            unsafe { check(BCryptExportKey(self.key.0,null_mut(),wide("ECCPUBLICBLOB").as_ptr(),blob.as_mut_ptr(),64,&mut used,0))?; }
            if used != 64 || blob[..4] != 0x504b4345u32.to_le_bytes() || blob[4..8] != 28u32.to_le_bytes() {
                return Err("invalid CNG P-224 public key".into());
            }
            Ok(blob[8..].try_into().unwrap())
        }

        pub fn exchange(&self, public: &[u8;56]) -> Result<[u8;28]> {
            let mut blob = [0;64];
            blob[..4].copy_from_slice(&0x504b4345u32.to_le_bytes());
            blob[4..8].copy_from_slice(&28u32.to_le_bytes());
            blob[8..].copy_from_slice(public);
            let mut key = Key(null_mut());
            let mut secret = Secret(null_mut());
            let mut shared = [0;28];
            let mut used = 0;
            unsafe {
                // Import validates the peer's point on the configured nistP224 curve.
                check(BCryptImportKeyPair(self.algorithm.0,null_mut(),wide("ECCPUBLICBLOB").as_ptr(),&mut key.0,blob.as_ptr(),64,0))?;
                check(BCryptSecretAgreement(self.key.0,key.0,&mut secret.0,0))?;
                check(BCryptDeriveKey(secret.0,wide("TRUNCATE").as_ptr(),null_mut(),shared.as_mut_ptr(),28,&mut used,0))?;
            }
            if used != 28 { return Err("invalid CNG P-224 shared secret length".into()); }
            shared.reverse();
            Ok(shared)
        }
    }
}

#[cfg(windows)]
pub use cng::KeyPair;

#[cfg(not(windows))]
pub struct KeyPair;

#[cfg(not(windows))]
impl KeyPair {
    pub fn generate() -> Result<Self> { Err("P-224 handshake requires Windows CNG".into()) }
    pub fn public(&self) -> Result<[u8;56]> { Err("P-224 handshake requires Windows CNG".into()) }
    pub fn exchange(&self, _: &[u8;56]) -> Result<[u8;28]> { Err("P-224 handshake requires Windows CNG".into()) }
}
