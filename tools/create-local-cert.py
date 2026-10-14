"""Create a private CA and localhost certificate; never touches OS trust stores."""
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

out = Path(__file__).resolve().parents[1] / 'runtime/certs'
if (out / 'ca.pem').exists():
    raise SystemExit('Existing certificate retained; no files changed.')
out.mkdir(parents=True, exist_ok=True)
now = datetime.now(timezone.utc)
ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'CODOL Local Revival CA')])
ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
      .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
      .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=365))
      .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
      .sign(ca_key, hashes.SHA256()))
server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
server = (x509.CertificateBuilder()
          .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, '127.0.0.1')]))
          .issuer_name(ca_name).public_key(server_key.public_key())
          .serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=365))
          .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ip_address('127.0.0.1')), x509.DNSName('localhost')]), critical=False)
          .add_extension(x509.ExtendedKeyUsage([x509.oid.ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
          .sign(ca_key, hashes.SHA256()))
for name, key in [('ca-key.pem', ca_key), ('server-key.pem', server_key)]:
    (out / name).write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
for name, cert in [('ca.pem', ca), ('server.pem', server)]:
    (out / name).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print('Local certificates created in', out)
