from Crypto.PublicKey import RSA

keyPair = RSA.generate(bits=1024)
print(f"Public key:  (N={hex(keyPair.n)}, e={hex(keyPair.e)})")
print()
print(f"Private key: (d={hex(keyPair.d)})")
