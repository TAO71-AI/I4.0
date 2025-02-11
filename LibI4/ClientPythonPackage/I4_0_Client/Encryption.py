from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import base64

def __parse_hash__(HashName: str) -> hashes.HashAlgorithm | None:
    if (HashName == "sha224"):
        return hashes.SHA224()
    elif (HashName == "sha256"):
        return hashes.SHA256()
    elif (HashName == "sha384"):
        return hashes.SHA384()
    elif (HashName == "sha512"):
        return hashes.SHA512()
    
    raise ValueError("Unsupported hash algorithm.")

def __split_message__(Message: bytes, MaxSize: int) -> list[bytes]:
    # Split the message into chunks
    return [Message[i:i + MaxSize] for i in range(0, len(Message), MaxSize)]

def CreateKeys() -> tuple[bytes, bytes]:
    # Generate the keys
    prKey = rsa.generate_private_key(public_exponent = 65537, key_size = 2048)
    puKey = prKey.public_key()

    # Get the private and public bytes
    prKey = prKey.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.PKCS8,
        encryption_algorithm = serialization.NoEncryption()
    )
    puKey = puKey.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Return the bytes of the keys
    return (prKey, puKey)

def DecryptMessage(Message: str | bytes, Key: str | bytes, HashAlgorithm: hashes.HashAlgorithm) -> str:
    # Encode the message
    if (isinstance(Message, bytes)):
        Message = Message.decode("utf-8")
    elif (not isinstance(Message, str)):
        raise Exception("Invalid message.")

    # Get the private key from the data
    if (isinstance(Key, str)):
        Key = Key.encode("utf-8")
    elif (not isinstance(Key, bytes)):
        raise Exception("Invalid key.")

    prKey = serialization.load_pem_private_key(Key, password = None)
    
    try:
        # Try to decode the message using base64
        Message = [base64.b64decode(chunk) for chunk in Message.split("|")] if (Message.count("|") > 0) else [base64.b64decode(Message)]
    except:
        # Error decoding the message, return the message (probably isn't encrypted)
        return Message

    # Create the chunks list
    decChunks = []

    for chunk in Message:
        # Decrypt using the private key
        message = prKey.decrypt(
            chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = HashAlgorithm),
                algorithm = HashAlgorithm,
                label = None
            )
        )

        # Append into the chunks list
        decChunks.append(message)

    # Return the message
    return b"".join(decChunks).decode("utf-8")

def EncryptMessage(Message: str | bytes, Key: str | bytes, HashAlgorithm: hashes.HashAlgorithm) -> str:
    # Encode the message
    if (isinstance(Message, str)):
        Message = Message.encode("utf-8")
    elif (not isinstance(Message, bytes)):
        raise Exception("Invalid message.")

    # Get the public key from the data
    if (isinstance(Key, str)):
        Key = Key.encode("utf-8")
    elif (not isinstance(Key, bytes)):
        raise Exception(f"Invalid key. Key is '{type(Key)}'.")

    puKey = serialization.load_pem_public_key(Key)
    puKeySize = puKey.key_size // 8
    hashSize = HashAlgorithm.digest_size
    maxMessageSize = puKeySize - 2 * hashSize - 2

    # Create the chunks list
    encChunks = []

    for chunk in __split_message__(Message, maxMessageSize):
        # Encrypt using the public key
        message = puKey.encrypt(
            chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = HashAlgorithm),
                algorithm = HashAlgorithm,
                label = None
            )
        )

        # Append into the chunks list
        encChunks.append(base64.b64encode(message).decode("utf-8"))

    # Return the message
    return "|".join(encChunks)