# RSA verify signature
msg = (input("Enter a message signed: ")).encode()
signature = int(input("Enter the signature received: "), 16)
N = int(input("Enter N : "), 16)
e = int(input("Enter e : "), 16)

from hashlib import sha512

hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
hashFromSignature = pow(signature, e, N)
print("Signature valid:", hash == hashFromSignature)
