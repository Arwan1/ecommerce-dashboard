import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

class SecurityManager:
    """
    Handles data encryption, decryption, and password hashing.
    """
    def hash_password(self, password):
        """Hashes a password for storing in the database using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password, hashed_password):
        """Verifies a plain password against a hashed one."""
        return self.hash_password(plain_password) == hashed_password

    def generate_rsa_keys(self):
        """
        Generates a new RSA public/private key pair.
        Returns:
            tuple: A tuple containing the private key and public key objects.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        return private_key, public_key

    def serialize_public_key(self, public_key):
        """Serializes a public key object into PEM format for storage."""
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    def serialize_private_key(self, private_key):
        """
        Serializes a private key object into PEM format.
        NOTE: This should be heavily secured, e.g., stored on an encrypted dongle as per the plan.
        """
        return private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption() # Or use a password
        )

    def encrypt_data(self, public_key_pem, data):
        """Encrypts data using an RSA public key."""
        public_key = serialization.load_pem_public_key(public_key_pem)
        
        # Ensure data is bytes
        if isinstance(data, str):
            data = data.encode('utf-8')
            
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt_data(self, private_key, ciphertext):
        """Decrypts data using an RSA private key."""
        # private_key object is passed directly, assuming it's loaded from a secure source (e.g., dongle)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext.decode('utf-8')
