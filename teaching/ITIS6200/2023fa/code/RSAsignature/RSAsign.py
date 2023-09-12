# RSA sign the message
N = int(input("Enter N : "), 16)
d = int(input("Enter d : "), 16)
hash = int(input("Enter the hash of message: "), 16)
signature = pow(hash, d, N)
print("Signature:", hex(signature))
