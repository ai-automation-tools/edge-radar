"""Kalshi request signing round-trips under the locked `cryptography` (no network)."""

import base64

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from kalshi_client import KalshiClient


def test_signature_verifies_and_ignores_the_query_string():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    client = KalshiClient(private_key_content=pem, base_url="https://demo-api.kalshi.co")
    path = "/trade-api/v2/portfolio/balance"
    sig = base64.b64decode(client._sign("1700000000000", "get", path + "?subaccount=0"))
    key.public_key().verify(  # raises InvalidSignature on mismatch
        sig,
        f"1700000000000GET{path}".encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )
