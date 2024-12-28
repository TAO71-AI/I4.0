from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import base64

PrivateKey: bytes = b""
PublicKey: bytes = b""
ServerPublicKey: bytes = b""

def __split_message__(Message: bytes, MaxSize: int) -> list[bytes]:
    # Split the message into chunks
    return [Message[i:i+MaxSize] for i in range(0, len(Message), MaxSize)]

def __create_keys__() -> None:
    global PrivateKey, PublicKey

    # Generate the keys
    prKey = rsa.generate_private_key(public_exponent = 65537, key_size = 2048)
    puKey = prKey.public_key()

    # Get private and public bytes
    PrivateKey = prKey.private_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm = serialization.NoEncryption()
    )
    PublicKey = puKey.public_bytes(
        encoding = serialization.Encoding.PEM,
        format = serialization.PublicFormat.SubjectPublicKeyInfo
    )

def DecryptMessage(Message: str | bytes) -> str:
    global PrivateKey

    # Get the private key from the data
    prKey = serialization.load_pem_private_key(PrivateKey, password = None)

    # Encode the message
    if (type(Message) is bytes):
        Message = Message.decode("utf-8")
    
    Message = [base64.b64decode(chunk) for chunk in Message.split("|")]

    # Create the chunks list
    decChunks = []

    for chunk in Message:
        # Decrypt using the private key
        message = prKey.decrypt(
            chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = hashes.SHA512()),
                algorithm = hashes.SHA512(),
                label = None
            )
        )

        # Append into the chunks list
        decChunks.append(message)

    # Return the message
    return b"".join(decChunks).decode("utf-8")

def EncryptMessage(Message: str | bytes, Key: str | bytes | None) -> str:
    global PublicKey

    # Get the public key from the data
    if (type(Key) is str):
        Key = Key.encode("utf-8")
    elif (type(Key) is None):
        Key = PublicKey

    puKey = serialization.load_pem_public_key(Key)

    # Encode the message
    if (type(Message) is str):
        Message = Message.encode("utf-8")

    # Create the chunks list
    encChunks = []

    for chunk in __split_message__(Message, 126):
        # Encrypt using the public key
        message = puKey.encrypt(
            chunk,
            padding.OAEP(
                mgf = padding.MGF1(algorithm = hashes.SHA512()),
                algorithm = hashes.SHA512(),
                label = None
            )
        )

        # Append into the chunks list
        encChunks.append(base64.b64encode(message).decode("utf-8"))

    # Return the message
    return "|".join(encChunks)