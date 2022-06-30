"""
init scoping, docs: 15 mins
building a basic server, unit test, and functioning endpoint: 15 mins
handling the "big number" async case: 30 mins
fixing bugs in how I handle cached results: 15 mins

Evaluating whether a given number is prime should not be an O(N)^2-ish problem. Seems to be np-complete
Once we have a number, it won't take long to divide every smaller number into it.
(actually it is NP-intermediate according to quora) But just in case, I'll have the API endpoint estimate the
time to complete based on the length (in digits) of the number and go asynchronous if the number is bigger
than 1 million. (I'll test to ensure that anything smaller returns in a reasonable time <3 sec)

For really really big numbers, it can
(1) immediately return a unique lookup code to the user,
(2) do the calculation for whatever time it takes
(3) then if the user requests the answer with the code (using the same endpoint),
it will return a status (e.g. PROCESSING) that might include the answer.
This avoids a more complicated backend architecture but delivers the best
performance at scale and would probably be workable with some frontend react app
(e.g. react pings every second until it is ready).

So there are actually TWO parts to the endpoint -- give it a number OR give it some lookup code
for the answer to some previous number.

If this needed to scale, I could cache all the answers as they were calculated and it could first
check the cache table for easy answers before calculating a new one, but seems like overkill.

Using the 'net I tested known primes up to 1299827 and it was fast (calculated dozens in <1s) so I'll set that as the limit.

async notes:
============

Before returning, flask spawns a subprocess that calculates the result and saves it to a local file store (JSON).
When ASI calls come in, it will check that file and return the result (or a result with the status "processing")
Last bug: had to pass key with test number to subprocess, otherwise it might not update multiple pending requests for same number.
"""

from flask import Flask, request, jsonify
import json
from random import choice
import threading
import subprocess
import shlex
import argparse

# I need a function that takes a number and returns true if it is a prime number
def is_prime(N):
    if not isinstance(N, int):
        try:
            N = int(N)
        except:
            return None
    if N == 1:
        return False # 1 isn't prime, because it can only be divided by 1 and itself.
    for i in range(2, N): # take every whole number up to N, divide it by N. If 0 left over, it's not prime.
        if N % i == 0:
            return False
    return True

# to start local server...
#$ export FLASK_APP=server (this filename)
#$ flask run
#* Running on http://127.0.0.1:5000/
app = Flask(__name__)
ASYNC_LIMIT   = 10000000 # >10 million is slow
COMPUTE_LIMIT = 10000000000 # > 10 billion is TOO slow to manage (will take hours? could be cached from public records.)
async_keys = {} # stores each key and the result dicts

def start_prime_check(command):
    subprocess.run(shlex.split(command), check=True)

@app.route("/", methods=['POST', 'GET'])
def test_N_is_prime():
    # some API calls are asynchronous; this handles them.
    if 'key' in request.args:
        key = request.args.get('key')
        with open('async_results.json', 'r') as f:
            async_keys = json.load(f)
        if key in async_keys:
            return async_keys[key]
        else:
            return {
                "error": True,
                "message": f"Key {key} not found.",
                "result": None,
            }
        # todo: if this was persistent I would routinely wipe these cached keys and results at regular intervals.
        # and this design doesn't reuse cached results for different requests. Must fix, because the async-result
        # looks for first instance of the number, so it won't update the latest one.

    # catch invalid or missing input
    N = request.args.get('n', None)
    try:
        N = int(N)
    except:
        if N is None:
            return {"result": None, "error": True, "message": "No data received. Submit your number like ?n=<some integer>"}
        return {"result": None, "error": True, "message": f"Did not understand {N}. Submit an integer number. (e.g. ...?n=5)"}

    if N > COMPUTE_LIMIT:
        # TODO: cache first 50 million primes for this mode: https://primes.utm.edu/lists/small/millions/
        return {"result": None, "error": True, "message": "Cannot test numbers greater than 10 billion"}
    # switch to asynchronous mode
    if N > ASYNC_LIMIT:
        # give user a lookup key instead
        digit = "1234567890"
        return_key = ''.join(choice(digit) for i in range(12))
        with open('async_results.json', 'r') as f:
            async_keys = json.load(f)
        async_keys[return_key] = {"result": None, "error": False, "message": "processing", "key":return_key, "n": N}
        with open('async_results.json', 'w') as f:
            json.dump(async_keys, f)
        # here we start a separate threaded subprocess to ruminate on the result
        #thread = threading.Thread(target=start_prime_check, args=(f'python','server.py',N))
        #thread.start()
        subprocess.Popen((f'python', 'server.py', str(N), '-k', str(return_key)))
        return {
            "result": None,
            "error": False,
            "message": f"{N} was too big to calculate immediately. You can request this result by appending ?key={return_key} to this API endpoint and receive a status or the eventual answer.",
            "key": return_key
        }

    return {"result": is_prime(N), "error": False, "message": None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='check whether integer is prime')
    parser.add_argument('number', metavar='N', type=int)
    parser.add_argument('-k', '--key', type=str)
    args = parser.parse_args()
    result = is_prime(args.number)
    # save result into the local file storage (sure, this won't work for massive concurrency, but I'd use a database for that)
    # or, I could use a separate file to pass EACH result and it would work for more concurrency
    with open('async_results.json', 'r') as f:
        data = json.load(f)
    if args.key not in data:
        print("ERROR: did not find this KEY in pending results") #<--- this message goes nowhere in a subprocess mode; only useful for testing.
        import sys;sys.exit()
    #key = [k for k,v in data.items() if v["n"] == args.number and k == args.key]
    this_result = data[args.key]
    this_result.update({"result": result, "message": "complete"} )
    data[args.key] = this_result
    print(this_result)
    with open('async_results.json', 'w') as f:
        json.dump(data, f)
