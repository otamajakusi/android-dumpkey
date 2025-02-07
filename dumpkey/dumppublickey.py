# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import os
import sys
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import load_pem_public_key
unistr = str if sys.version_info >= (3, 0) else unicode
def gcd(a, b):
    # Return the GCD of a and b using Euclid's Algorithm
    while a != 0:
        a, b = b % a, a
    return b


def findModInverse(a, m):
    # Cryptomath Module
    # http://inventwithpython.com/hacking (BSD Licensed)

    # Returns the modular inverse of a % m, which is
    # the number x such that a*x % m = 1

    if gcd(a, m) != 1:
        return None # no mod inverse if a & m aren't relatively prime

    # Calculate using the Extended Euclidean Algorithm:
    u1, u2, u3 = 1, 0, a
    v1, v2, v3 = 0, 1, m
    while v3 != 0:
        q = u3 // v3 # // is the integer division operator
        v1, v2, v3, u1, u2, u3 = (u1 - q * v1), (u2 - q * v2), (u3 - q * v3), v1, v2, v3
    return u1 % m


def check(pubkey):
    """
    :param pubkey:  EVP_PKEY
    """
    rsa = pubkey.public_numbers()
    pubexp = rsa.e
    # modulus = int(rsa.n, 16)
    modulus = rsa.n
    expect = (3, 65537)
    if pubexp not in expect:
        raise Exception("Public exponent should be in %s but is %s " % (expect, pubexp ))

    if modulus.bit_length() != 2048:
        raise Exception("Modulus should be 2048 bits long but is %s bits" % modulus.bit_length())


def print_rsa(pubkey):
    """
    :param pubkey: EVP_PKEY | str
    """

    if type(pubkey) is unistr:
        if not os.path.exists(pubkey):
            raise Exception("%s does not exist" % pubkey)
        try:
            with open(pubkey, 'rb') as pubkeyfile:
                tcs = x509.load_pem_x509_certificate(pubkeyfile.read(), default_backend())
            pubkey = tcs.public_key()
        except ValueError as cert_err:
            # It may be just a public key
            try:
                with open(pubkey, 'rb') as pubkeyfile:
                    pubkey = load_pem_public_key(pubkeyfile.read(), default_backend())
            except ValueError as key_error:
                raise Exception('%s is not parseable as a certificate or public key' % pubkey)
        
    check(pubkey)

    N = pubkey.public_numbers().n
    result = ""
    key_bit_length = N.bit_length()

    nwords = N.bit_length() // 32 # of 32 bit integers in modulus

    '''
    result += "{"
    result += str(nwords)
    '''

    B = 2 ** 32
    N0inv = int(B - findModInverse(N, B))

    result += "const uint32_t rsa_n0inv = "
    result += hex(N0inv)
    result += ";\n\n"

    R = 2 ** N.bit_length()
    RR = (R * R) % N  #2^4096 mod N

    result += "const uint32_t rsa_N[] = {\n\t"

    # Write out modulus as `big` endian array of integers.
    N_big = int.from_bytes(N.to_bytes(key_bit_length // 8, 'little'), 'big')
    for i in range(0, nwords):
        n = N_big % B
        result += f"0x{n:08x}"

        if i != nwords - 1:
            result += ","
        if (i + 1) % 4 == 0:
            if (i + 1) != nwords:
                result += "\n\t"
            else:
                result += "\n"

        N_big = N_big // B

    result += "};\n\n"

    # Write R^2 as `big` endian array of integers.
    result += "const uint32_t rsa_rr[] = {\n\t"

    RR_big = int.from_bytes(RR.to_bytes(key_bit_length // 8, 'little'), 'big')
    for i in range(0, nwords):
        rr = RR_big % B
        result += f"0x{rr:08x}"

        if i != nwords -1:
            result += ","
        if (i + 1) % 4 == 0:
            if (i + 1) != nwords:
                result += "\n\t"
            else:
                result += "\n"

        RR_big = RR_big // B

    result += "};"
    return result
