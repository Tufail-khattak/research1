import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# Ensure the "keys" directory exists
if not os.path.exists("keys"):
    os.makedirs("keys")


def generate_key_pair(name):
    # Generate RSA private and public key pair
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # Export private key
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Export public key
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo  # Correct format
    )

    # Save the private key to a file
    with open(f"keys/{name}_priv.pem", "wb") as f:
        f.write(private_pem)

    # Save the public key to a file
    with open(f"keys/{name}_pub.pem", "wb") as f:
        f.write(public_pem)


# Generate key pairs for client, ws (web server), and sms (session management server)
for entity in ["client", "ws", "sms"]:
    generate_key_pair(entity)
