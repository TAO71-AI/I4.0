# Import libraries
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from concurrent.futures import ThreadPoolExecutor
import base64
import os
import json

def __parse_hash__(HashName: str) -> hashes.HashAlgorithm | None:
    if (HashName == "sha224"):
        return hashes.SHA224()
    elif (HashName == "sha256"):
        return hashes.SHA256()
    elif (HashName == "sha384"):
        return hashes.SHA384()
    elif (HashName == "sha512"):
        return hashes.SHA512()
    elif (HashName == "none"):
        return None
    
    raise ValueError("Unsupported hash algorithm.")

def __split_message__(Message: bytes, MaxSize: int) -> list[bytes]:
    return [Message[i:i + MaxSize] for i in range(0, len(Message), MaxSize)]

def CreateKeys() -> tuple[bytes, bytes]:
    prKey = rsa.generate_private_key(public_exponent = 65537, key_size = 2048)
    puKey = prKey.public_key()

    prKey = prKey.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.PKCS8,
        encryption_algorithm = serialization.NoEncryption()
    )
    puKey = puKey.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return (prKey, puKey)

def __is_hybrid_message__(Message: str) -> bool:
    try:
        parsed = json.loads(Message)
        return "key" in parsed and "data" in parsed and "iv" in parsed
    except:
        return False

def EncryptMessage(Message: str | bytes, Key: str | bytes, HashAlgorithm: hashes.HashAlgorithm | None, UseHybrid: bool = False) -> str:
    # Check if the hash algorithm is null
    if (HashAlgorithm is None):
        return Message.decode("utf-8") if (isinstance(Message, bytes)) else Message

    # Encrypt
    if (UseHybrid):
        return __encrypt_hybrid__(Message, Key, HashAlgorithm)
    else:
        return __encrypt_rsa__(Message, Key, HashAlgorithm)

def __encrypt_rsa__(Message: str | bytes, Key: str | bytes, HashAlgorithm: hashes.HashAlgorithm) -> str:
    if (isinstance(Message, str)):
        Message = Message.encode("utf-8")
    elif (not isinstance(Message, bytes)):
        raise Exception("Invalid message.")

    if (isinstance(Key, str)):
        Key = Key.encode("utf-8")
    elif (not isinstance(Key, bytes)):
        raise Exception(f"Invalid key. Key is '{type(Key)}'.")

    puKey = serialization.load_pem_public_key(Key)
    puKeySize = puKey.key_size // 8
    hashSize = HashAlgorithm.digest_size
    maxMessageSize = puKeySize - 2 * hashSize - 2
    
    chunks = __split_message__(Message, maxMessageSize)

    def enc(Chunk: bytes) -> str:
        encrypted = puKey.encrypt(
            Chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = HashAlgorithm),
                algorithm = HashAlgorithm,
                label = None
            )
        )
        return base64.b64encode(encrypted).decode("utf-8")

    with ThreadPoolExecutor() as executor:
        encChunks = list(executor.map(enc, chunks))

    return "|".join(encChunks)

def __encrypt_hybrid__(Message: str | bytes, Key: str | bytes, HashAlgorithm: hashes.HashAlgorithm) -> str:
    if (isinstance(Message, str)):
        Message = Message.encode("utf-8")
    elif (not isinstance(Message, bytes)):
        raise Exception("Invalid message.")

    if (isinstance(Key, str)):
        Key = Key.encode("utf-8")
    elif (not isinstance(Key, bytes)):
        raise Exception("Invalid key.")

    puKey = serialization.load_pem_public_key(Key)
    aesKey = os.urandom(32)
    iv = os.urandom(16)

    # AES Encrypt
    cipher = Cipher(algorithms.AES(aesKey), modes.CBC(iv), backend = default_backend())
    encryptor = cipher.encryptor()
    padLength = 16 - (len(Message) % 16)
    paddedMessage = Message + bytes([padLength] * padLength)
    aesEncrypted = encryptor.update(paddedMessage) + encryptor.finalize()

    # RSA Encrypt key
    encryptedKey = puKey.encrypt(
        aesKey,
        padding.OAEP(
            mgf = padding.MGF1(algorithm = HashAlgorithm),
            algorithm = HashAlgorithm,
            label = None
        )
    )

    # Return as JSON base64
    return json.dumps({
        "key": base64.b64encode(encryptedKey).decode("utf-8"),
        "data": base64.b64encode(aesEncrypted).decode("utf-8"),
        "iv": base64.b64encode(iv).decode("utf-8")
    })

def DecryptMessage(Message: str | bytes, Key: str | bytes, HashAlgorithm: hashes.HashAlgorithm | None) -> str:
    if (isinstance(Message, bytes)):
        Message = Message.decode("utf-8")
    elif (not isinstance(Message, str)):
        raise RuntimeError("Invalid message.")

    if (isinstance(Key, str)):
        Key = Key.encode("utf-8")
    elif (not isinstance(Key, bytes)):
        raise RuntimeError("Invalid key.")

    if (HashAlgorithm is None):
        return Message

    if (__is_hybrid_message__(Message)):
        return __decrypt_hybrid__(Message, Key, HashAlgorithm)
    else:
        return __decrypt_rsa__(Message, Key, HashAlgorithm)

def __decrypt_rsa__(Message: str, Key: bytes, HashAlgorithm: hashes.HashAlgorithm) -> str:
    prKey = serialization.load_pem_private_key(Key, password=None)

    try:
        chunks = [base64.b64decode(chunk) for chunk in Message.split("|")] if ("|" in Message) else [base64.b64decode(Message)]
    except:
        return Message

    def dec(Chunk: bytes) -> bytes:
        return prKey.decrypt(
            Chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = HashAlgorithm),
                algorithm = HashAlgorithm,
                label = None
            )
        )

    with ThreadPoolExecutor() as executor:
        decChunks = list(executor.map(dec, chunks))

    return b"".join(decChunks).decode("utf-8")

def __decrypt_hybrid__(Message: str, Key: bytes, HashAlgorithm: hashes.HashAlgorithm) -> str:
    prKey = serialization.load_pem_private_key(Key, password=None)
    parsed = json.loads(Message)

    aesKey = prKey.decrypt(
        base64.b64decode(parsed["key"]),
        padding.OAEP(
            mgf = padding.MGF1(algorithm = HashAlgorithm),
            algorithm = HashAlgorithm,
            label = None
        )
    )

    cipher = Cipher(
        algorithms.AES(aesKey),
        modes.CBC(base64.b64decode(parsed["iv"])),
        backend = default_backend()
    )

    decryptor = cipher.decryptor()
    padded = decryptor.update(base64.b64decode(parsed["data"])) + decryptor.finalize()
    padLength = padded[-1]

    return padded[:-padLength].decode("utf-8")