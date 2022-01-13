Shaduf implementation
=
The smart contract is in shaduf.sol.


Shaduf simulation
=
The performance, payment success ratio and volume, of Shaduf, Revive, and OPT-Revive in the Lightning network.

Requirements:
-
Python >= 3.7.3
curl
numpy 
networkx
random
scipy
json
functools
collections


Steps:
-
1. Generate the Lightning network topology at 2020-03-31
    + Get the channels from https://ln.bigsun.xyz/
    > curl 'https://ln.fiatjaf.com/api/channels?open->>block=gte.1&open->>block=lt.600001' > channel_1_600000.json
    
    > curl 'https://ln.fiatjaf.com/api/channels?open->>block=gte.600001&open->>block=lt.677168' > channel_600001_677167.json

    + Generate the network topology using network/generate_network.py

2. Get the Bitcoin payment value in 2020-03 using payment_value/get_payment_value.py  
3. Get the Shaduf's performance using shaduf.py
4. Get the Revive's performance using revive.py
5. Get the OPT-Revive's performance using opt_revive.py
6. Compare the results