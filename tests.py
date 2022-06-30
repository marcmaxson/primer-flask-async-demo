import pytest
import server
import random

class TestPrimer():

    def test_is_prime(self):
        test_numbers = {1:0, 3:1,5:1,7:1,9:0,12:0,15:0,18:0,21:0,24:0,27:0,
            563:1, 653:1, 659:1, 953:1, 30029:1, 65537:1, 123456:0, 1297799:1, 1299821:1, 1299827:1}
        # -- 9999999929:1 -- this LAST one will run for a LONG time
        # note that True == 1 and False == 0 in python logic.
        for N,result in test_numbers.items():
            if server.is_prime(N) != result:
                raise Exception(f'{N} fails is_prime test')
