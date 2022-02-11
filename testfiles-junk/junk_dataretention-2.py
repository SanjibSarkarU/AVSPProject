import time

import junkdataretention


for i in range(100, 1000):
    a = junkdataretention.data_retention(i,i,1, i, retentionsize= 5)
    print(a)
    time.sleep(1)