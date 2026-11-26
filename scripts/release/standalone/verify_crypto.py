# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Offline checks for an extracted CLI package.

Run with the package's Python: python -S verify_crypto.py --packages <site-packages>.
On macOS, also pass --architecture arm64|x86_64 --python-formula python@3.14.
Temporary TLS files are created under the working directory and removed after use.
"""

import argparse
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
from pathlib import Path
import platform
import ssl
import subprocess
import sys
import tempfile
import threading


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def resolve_library(name, binary, rpaths):
    if name == "@loader_path":
        return binary.parent
    if name.startswith("@loader_path/"):
        return binary.parent / name.removeprefix("@loader_path/")
    if name == "@executable_path":
        return Path(sys.executable).parent
    if name.startswith("@executable_path/"):
        return Path(sys.executable).parent / name.removeprefix("@executable_path/")
    if name.startswith("@rpath/"):
        for rpath in rpaths:
            root = resolve_library(rpath, binary, [])
            candidate = root / name.removeprefix("@rpath/")
            if candidate.exists():
                return candidate
        raise RuntimeError(f"Unresolved library {name} in {binary}")
    path = Path(name)
    if not path.is_absolute():
        raise RuntimeError(f"Unsupported library path {name} in {binary}")
    return path


def verify_macos_libraries(packages, architecture, python_formula):
    if platform.machine() != architecture:
        raise RuntimeError(f"Expected {architecture}, got {platform.machine()}")
    formulas = [python_formula, *command("brew", "deps", "--formula", python_formula).splitlines()]
    allowed_roots = [packages, *(Path(command("brew", "--prefix", formula)).resolve()
                                for formula in formulas)]
    print(command("brew", "list", "--versions", *formulas))
    binaries = list((packages / "cryptography").rglob("*.so"))
    if not binaries:
        raise RuntimeError("No packaged cryptography native extensions found")
    visited = set()
    while binaries:
        binary = binaries.pop().resolve(strict=True)
        if binary in visited:
            continue
        visited.add(binary)
        print(command("file", str(binary)))
        subprocess.run(["lipo", str(binary), "-verify_arch", architecture], check=True)
        linkage = command("otool", "-L", str(binary))
        print(linkage)
        load_commands = command("otool", "-l", str(binary)).splitlines()
        rpaths = []
        install_name = None
        for index, line in enumerate(load_commands):
            if line.strip() == "cmd LC_RPATH":
                rpaths.append(load_commands[index + 2].strip().removeprefix("path ").rsplit(" (offset ", 1)[0])
            elif line.strip() == "cmd LC_ID_DYLIB":
                install_name = load_commands[index + 2].strip().removeprefix("name ").rsplit(" (offset ", 1)[0]
        for line in linkage.splitlines()[1:]:
            name = line.strip().split(" (", 1)[0]
            if name == install_name:
                continue
            if name.startswith(("/usr/lib/", "/System/Library/")):
                continue
            library = resolve_library(name, binary, rpaths)
            if str(library).startswith(("/usr/lib/", "/System/Library/")):
                continue
            library = library.resolve(strict=True)
            if not any(library.is_relative_to(root) for root in allowed_roots):
                raise RuntimeError(f"Undeclared native dependency: {library} required by {binary}")
            binaries.append(library)
    print("Native architecture and dependency checks passed")


def verify_operations(packages):
    import cryptography
    import OpenSSL
    import paramiko
    import requests
    import urllib3
    from cryptography import x509
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.backends.openssl.backend import backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.serialization import pkcs12

    for module in (cryptography, OpenSSL, paramiko, requests, urllib3):
        if not Path(module.__file__).resolve().is_relative_to(packages):
            raise RuntimeError(f"{module.__name__} loaded outside the artifact: {module.__file__}")
        print(f"{module.__name__} {module.__version__}: {module.__file__}")
    print(f"Python: {sys.version}")
    print(f"cryptography backend: {backend.openssl_version_text()}")
    print(f"Python TLS backend: {ssl.OPENSSL_VERSION}")

    message = b"Azure CLI cryptography smoke test"
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption())
    key = serialization.load_pem_private_key(pem, password=None)
    signature = key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    key.public_key().verify(signature, message, padding.PKCS1v15(), hashes.SHA256())
    print("RSA key generation, PEM round-trip and signature verification passed")

    cipher = AESGCM(AESGCM.generate_key(bit_length=256))
    nonce = b"\x00" * 12
    ciphertext = cipher.encrypt(nonce, message, b"azure-cli")
    assert cipher.decrypt(nonce, ciphertext, b"azure-cli") == message
    try:
        cipher.decrypt(nonce, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]), b"azure-cli")
    except InvalidTag:
        pass
    else:
        raise AssertionError("AES-GCM accepted corrupted ciphertext")
    print("AES-GCM round-trip and tamper rejection passed")

    ssh_key = ed25519.Ed25519PrivateKey.generate()
    ssh_pem = ssh_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.OpenSSH,
                                   serialization.NoEncryption())
    restored = serialization.load_ssh_private_key(ssh_pem, password=None)
    restored.public_key().verify(restored.sign(message), message)
    public = restored.public_key().public_bytes(serialization.Encoding.OpenSSH,
                                               serialization.PublicFormat.OpenSSH)
    paramiko_key = paramiko.Ed25519Key.from_private_key(io.StringIO(ssh_pem.decode("ascii")))
    assert f"{paramiko_key.get_name()} {paramiko_key.get_base64()}".encode("ascii") == public
    ssh_signature = paramiko_key.sign_ssh_data(message)
    paramiko_public = paramiko.Ed25519Key(data=paramiko_key.asbytes())
    assert paramiko_public.verify_ssh_sig(message, paramiko.Message(ssh_signature.asbytes()))
    print("Ed25519 OpenSSH round-trip and Paramiko signatures passed")

    name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "localhost")])
    now = datetime.now(timezone.utc)
    certificate = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=5))
                   .not_valid_after(now + timedelta(days=1))
                   .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
                   .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
                   .sign(key, hashes.SHA256()))
    cert_pem = certificate.public_bytes(serialization.Encoding.PEM)
    loaded = x509.load_pem_x509_certificate(cert_pem)
    assert loaded.fingerprint(hashes.SHA256()) == certificate.fingerprint(hashes.SHA256())
    openssl_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_pem)
    assert openssl_cert.to_cryptography().fingerprint(hashes.SHA256()) == loaded.fingerprint(hashes.SHA256())
    pfx = pkcs12.serialize_key_and_certificates(
        b"smoke-test", key, certificate, None, serialization.BestAvailableEncryption(b"smoke-test"))
    pfx_key, pfx_cert, _ = pkcs12.load_key_and_certificates(pfx, b"smoke-test")
    assert pfx_key.public_key().public_numbers() == key.public_key().public_numbers()
    assert pfx_cert.fingerprint(hashes.SHA256()) == loaded.fingerprint(hashes.SHA256())
    try:
        pkcs12.load_key_and_certificates(pfx, b"wrong-password")
    except ValueError:
        pass
    else:
        raise AssertionError("PKCS#12 accepted the wrong password")
    print("X.509/pyOpenSSL and password-protected PKCS#12 checks passed")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(message)

    with tempfile.TemporaryDirectory(prefix="crypto-smoke-", dir=Path.cwd()) as directory:
        root = Path(directory)
        cert_path = root / "certificate.pem"
        key_path = root / "key.pem"
        cert_path.write_bytes(cert_pem)
        key_path.write_bytes(pem)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            server.socket = context.wrap_socket(server.socket, server_side=True)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with requests.Session() as session:
                    session.trust_env = False
                    url = f"https://localhost:{server.server_port}/"
                    response = session.get(url, verify=str(cert_path), timeout=10)
                    response.raise_for_status()
                    assert response.content == message
                with requests.Session() as session:
                    session.trust_env = False
                    try:
                        session.get(url, verify=True, timeout=10)
                    except requests.exceptions.SSLError:
                        pass
                    else:
                        raise AssertionError("HTTPS accepted an untrusted certificate")
            finally:
                server.shutdown()
                worker.join(timeout=10)
    print("Requests/urllib3 local HTTPS trust and untrusted-certificate rejection passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", required=True, type=Path)
    parser.add_argument("--architecture", choices=("arm64", "x86_64"))
    parser.add_argument("--python-formula")
    args = parser.parse_args()
    packages = args.packages.resolve(strict=True)
    sys.path.insert(0, str(packages))
    if platform.system() == "Darwin":
        if not args.architecture or not args.python_formula:
            parser.error("macOS requires --architecture and --python-formula")
        verify_macos_libraries(packages, args.architecture, args.python_formula)
    elif args.architecture or args.python_formula:
        parser.error("macOS linkage checks require a macOS host")
    else:
        print("Non-macOS host: native macOS architecture/linkage checks are not run")
    verify_operations(packages)


if __name__ == "__main__":
    main()
