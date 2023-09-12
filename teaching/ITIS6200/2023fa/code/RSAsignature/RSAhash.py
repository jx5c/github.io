
msg = (input("Enter a message to hash: ")).encode()


from hashlib import sha512
hash = int.from_bytes(sha512(msg).digest(), byteorder='big')
print("Signature:", hex(hash))
