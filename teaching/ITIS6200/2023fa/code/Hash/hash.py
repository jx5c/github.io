# Python 3 code to demonstrate the
# working of MD5 (string - hexadecimal)

import hashlib

# initializing string
input = "Alice's grade is A!"
# input = "Alice's grade is A! Bob's grade is D!"

# encoding GeeksforGeeks using encode()
# then sending to md5()
result = hashlib.md5(input.encode())

# printing the equivalent hexadecimal value.
print("The hexadecimal equivalent of hash is : ", end ="")
print(result.hexdigest())
