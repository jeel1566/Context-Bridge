"""Generate Chrome extension key for manifest.json"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import base64

# Generate RSA key
key = rsa.generate_private_key(
    public_exponent=65537, 
    key_size=2048, 
    backend=default_backend()
)

# Get public key in DER format
pub_der = key.public_key().public_bytes(
    encoding=serialization.Encoding.DER,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

# Base64 encode
key_b64 = base64.b64encode(pub_der).decode('ascii')

print("=" * 60)
print("Add this to manifest.json as the 'key' field:")
print("=" * 60)
print()
print(key_b64)
print()
print("=" * 60)
