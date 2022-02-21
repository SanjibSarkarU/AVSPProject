import time
import logging
import junkdataretention

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

file_handler = logging.FileHandler('sample.log')
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# logger.addHandler(file_handler)
logger.addHandler(stream_handler)

for i in range(1, 10):
    a = junkdataretention.data_retention(i, i, 1, i, retentionsize= 5)
    # print(a)
    logger.info('SAVED')
    time.sleep(1)
