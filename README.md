# primer-flask-async-demo
Simple flask server with API endpoint that checks whether a number is prime, handling BIG numbers asynchronously.

## Time spent:

- init scoping, docs: 15 mins
- building a basic server, unit test, and functioning endpoint: 15 mins
- handling the "big number" async case: 30 mins
- fixing bugs in how I handle cached results: 15 mins
- setting up repo, pushing, tidying docs: 10 mins

## Thought process:

Evaluating whether a given number is prime should not be an O(N)^2-ish problem. Seems to be np-complete
Once we have a number, it won't take long to divide every smaller number into it.
(actually it is NP-intermediate according to quora) But just in case, I'll have the API endpoint estimate the
time to complete based on the length (in digits) of the number and go asynchronous if the number is bigger
than 1 million. (I'll test to ensure that anything smaller returns in a reasonable time <3 sec)

For really really big numbers, it can

- (1) immediately return a unique lookup code to the user,
- (2) do the calculation for whatever time it takes
- (3) then if the user requests the answer with the code (using the same endpoint),
- It will return a status (e.g. PROCESSING) that might include the answer.

This avoids a more complicated backend architecture but delivers the best
performance at scale and would probably be workable with some frontend react app
(e.g. react pings every second until it is ready).

So there are actually TWO parts to the endpoint -- give it a number OR give it some lookup code
for the answer to some previous number.

If this needed to scale, I could cache all the answers as they were calculated and it could first
check the cache table for easy answers before calculating a new one, but seems like overkill.

Using the 'net I tested known primes up to 1299827 and it was fast (calculated dozens in <1s) so I'll set that as the limit.

Async notes:
============

Before returning, flask spawns a subprocess that calculates the result and saves it to a local file store (JSON).
When ASI calls come in, it will check that file and return the result (or a result with the status "processing")
Last bug: had to pass key with test number to subprocess, otherwise it might not update multiple pending requests for same number.
