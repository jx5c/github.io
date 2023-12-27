# Diffie-Hellman Code


def prime_checker(p):
	# Checks If the number entered is a Prime Number or not
	if p < 1:
		return -1
	elif p > 1:
		if p == 2:
			return 1
		for i in range(2, p):
			if p % i == 0:
				return -1
			return 1


def primitive_check(g, p, L):
	# Checks If The Entered Number Is A Primitive Root Or Not
	for i in range(1, p):
		L.append(pow(g, i) % p)
	for i in range(1, p):
		if L.count(i) > 1:
			L.clear()
			return -1
		return 1


l = []
while 1:
	P = int(input("Enter P : "))
	if prime_checker(P) == -1:
		print("Number Is Not Prime, Please Enter Again!")
		continue
	break

while 1:
	G = int(input("Enter G : "))
	if prime_checker(G) == -1:
		print("Number Is Not Prime, Please Enter Again!")
		continue
	break

# Private Keys
a, b = int(input("Enter The Private Key Of Alice (a): ")), int(
	input("Enter The Private Key Of Bob (b): "))
while 1:
	if a >= P or b >= P:
		print(f"Private Key Of Both Should Be Less Than {P}!")
		continue
	break

# Calculate Public Keys
y1, y2 = pow(G, a) % P, pow(G, b) % P
print(f"\nInformation sent by Alice to Bob is pow(G, a) % P = pow({G}, {a}) % {P} = {pow(G, a)} % {P} = {y1}\nInformation sent by Bob to Alice Is pow(G, a) % P = pow({G}, {b}) % {P} = {pow(G, b)} % {P} = {y2}\n")

# Generate Secret Keys
k1, k2 = pow(y2, a) % P, pow(y1, b) % P
print(f"\nSecret Key For Alice Is pow({y2}, a) % P = pow({y2}, {a}) % {P} = {pow(y2, a)} % {P} = {k1}\nSecret Key For Bob Is pow({y1}, b) % P = pow({y1}, {b}) % {P} = {pow(y1, b)} % {P} = {k2}\n")


if k1 == k2:
	print("Keys Have Been Exchanged Successfully")
else:
	print("Keys Have Not Been Exchanged Successfully")
