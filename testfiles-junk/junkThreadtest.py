import time

import threading
import datetime
from collections import deque

i = 0


def send_through_continuously(t):
    send_through_ac_every = t
    x = datetime.datetime.now()
    threading.Timer(send_through_ac_every, send_through_continuously, args=(t,)).start()
    print(x)
    time.sleep(0.1)



send_through_continuously(t =2)

# d = deque(maxlen=5)
# for i in range (100):
#     d.append(i)
#     print(d)
