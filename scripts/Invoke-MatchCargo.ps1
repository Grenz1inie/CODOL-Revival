param([Parameter(ValueFromRemainingArguments=$true)][string[]]$CargoArgs)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$localCargo = Join-Path $projectRoot 'runtime/toolchains/cargo/bin/cargo.exe'
if (Test-Path -LiteralPath $localCargo) {
    $env:CARGO_HOME = Join-Path $projectRoot 'runtime/toolchains/cargo'
    $env:RUSTUP_HOME = Join-Path $projectRoot 'runtime/toolchains/rustup'
    $env:PATH = (Split-Path $localCargo -Parent) + ';' + $env:PATH
    $cargo = $localCargo
} else {
    $cargo = (Get-Command cargo.exe -ErrorAction Stop).Source
}
if (Test-Path -LiteralPath 'A:/Coding/mingw64/bin/x86_64-w64-mingw32-gcc.exe') {
    $env:CARGO_TARGET_X86_64_PC_WINDOWS_GNU_LINKER = 'A:/Coding/mingw64/bin/x86_64-w64-mingw32-gcc.exe'
    $env:PATH = 'A:/Coding/mingw64/bin;' + $env:PATH
}
$env:CARGO_TARGET_DIR = Join-Path $projectRoot 'runtime/build/rust-match'
Push-Location (Join-Path $projectRoot 'native/match-server')
try { & $cargo @CargoArgs; $result = $LASTEXITCODE }
finally { Pop-Location }
exit $result
