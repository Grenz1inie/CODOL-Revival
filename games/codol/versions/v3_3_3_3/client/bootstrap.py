"""Prepare this installation's local TLS identity and three client configuration files."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from ipaddress import ip_address
from pathlib import Path
import ssl
import sys
import tempfile
import time

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from games.codol.versions.v3_3_3_3.client.preparation import CLIENT_SHA256

def write_file(path, data):
    temporary = path.with_name(path.name + '.tmp')
    try:
        temporary.write_bytes(data)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def certificate_errors(directory):
    directory = Path(directory)
    try:
        ca = x509.load_pem_x509_certificate((directory / 'ca.pem').read_bytes())
        server = x509.load_pem_x509_certificate((directory / 'server.pem').read_bytes())
        now = datetime.now(timezone.utc)
        for name, cert in (('ca.pem', ca), ('server.pem', server)):
            if not cert.not_valid_before_utc <= now <= cert.not_valid_after_utc:
                return [f'{name}: certificate expired or not yet valid; check the clock and local certificates.']
        server.verify_directly_issued_by(ca)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.set_ciphers('ALL:@SECLEVEL=0')
        context.load_cert_chain(directory / 'server.pem', directory / 'server-key.pem')
    except (ValueError, OSError, TypeError, InvalidSignature) as error:
        return [f'Local certificate check failed: {error or type(error).__name__}']
    return []


def prepare_certificates(runtime):
    runtime = Path(runtime)
    directory = runtime / 'certs'
    if not certificate_errors(directory):
        return directory
    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CODOL Local Revival CA')])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=365))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    server = (x509.CertificateBuilder()
              .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, '127.0.0.1')]))
              .issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=365))
              .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
              .add_extension(x509.SubjectAlternativeName([
                  x509.IPAddress(ip_address('127.0.0.1')), x509.DNSName('localhost')]), critical=False)
              .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
              .sign(ca_key, hashes.SHA256()))
    runtime.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.certs-', dir=runtime) as temporary:
        stage = Path(temporary)
        for name, value in (('ca.pem', ca), ('server.pem', server)):
            (stage / name).write_bytes(value.public_bytes(serialization.Encoding.PEM))
        for name, value in (('ca-key.pem', ca_key), ('server-key.pem', key)):
            (stage / name).write_bytes(value.private_bytes(serialization.Encoding.PEM,
                      serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        backup = runtime / 'backups' / f'certs-{time.time_ns()}'
        if directory.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            directory.rename(backup)
        try:
            stage.rename(directory)
        except OSError:
            if backup.exists(): backup.rename(directory)
            raise
    return directory


def prepare(game, runtime):
    game, runtime = Path(game).resolve(), Path(runtime).resolve()
    with (game / 'codoMP_client_shipRetail.exe').open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != CLIENT_SHA256:
            raise ValueError('client hash mismatch: select the supported 3.3.3.3 installation')
    certificates = prepare_certificates(runtime)
    ca = (certificates / 'ca.pem').read_bytes()
    trust = (game / 'cacert.pem').read_bytes() if (game / 'cacert.pem').exists() else b''
    if ca.replace(b'\r\n', b'\n').strip() not in trust.replace(b'\r\n', b'\n'):
        trust += (b'\n' if trust and not trust.endswith(b'\n') else b'') + ca
    values = {'dwauth.ini': b'127.0.0.1 3074\n127.0.0.1 443\n0x03EA\n',
              'stun.ini': b'127.0.0.1\n', 'cacert.pem': trust}
    before = {name: (game / name).read_bytes() if (game / name).exists() else None for name in values}
    backup = runtime / 'backups/client-config'
    backup.mkdir(parents=True, exist_ok=True)
    if not (backup / 'missing.json').exists():
        for name, data in before.items():
            if data is not None: write_file(backup / name, data)
        write_file(backup / 'missing.json', json.dumps([n for n, data in before.items() if data is None]).encode())
    changed = []
    try:
        for name, data in values.items():
            if before[name] != data:
                write_file(game / name, data)
                changed.append(name)
    except OSError:
        for name in reversed(changed):
            if before[name] is None: (game / name).unlink(missing_ok=True)
            else: write_file(game / name, before[name])
        raise
    return certificates


def main():
    import argparse
    from games.codol.versions.v3_3_3_3.client.checks import check_environment
    from games.codol.versions.v3_3_3_3.client.preparation import prepare as prepare_resources
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'game', 'runtime'): parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    try:
        errors = check_environment(args.root, args.game, args.runtime, before_preparation=True)
        if errors: raise ValueError('\n'.join(errors))
        prepare_resources(args.root, args.game)
        prepare(args.game, args.runtime)
        errors = check_environment(args.root, args.game, args.runtime)
        if errors: raise ValueError('\n'.join(errors))
    except (OSError, ValueError, RuntimeError) as error:
        print(f'[FAIL] {error}')
        return 1
    print('Local client and Nuketown resources ready.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
