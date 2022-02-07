import threading
import time
from queue import Queue

received_func_inbox = Queue()


class Container:
    def __init__(self, info, weight, q):
        self.packet = None
        self.info = info
        self.weight = weight
        self.q = q

    def message(self):
        return self.info

    def priority(self):
        return self.weight

    def que(self):
        return self.q


def sender1():
    sender1_return_queue = Queue()
    send_request_osd = Container(info = 'xyz', weight = 1, q = sender1_return_queue)
    for i in range(10):
        received_func_inbox.put(send_request_osd)
        print('Sender1 is sending', send_request_osd)
        if not sender1_return_queue.empty():
            message_received = sender1_return_queue.get()
            print('MessageReceived1: ', message_received)
        time.sleep(10)


def sender2():
    sender2_return_queue = Queue()
    for i in range(10):
        send_request_osd = Container(message='xyz', priority=1, que=sender2_return_queue)
        received_func_inbox.put(send_request_osd)
        print('Sender2 is sending', send_request_osd)
        if not sender2_return_queue.empty():
            message_received = sender2_return_queue.get()
            print('MessageReceived2: ',message_received)
            print(message_received)
        time.sleep(20)


def received_func():
    lst = []
    while True:
        while not received_func_inbox.empty():
            lst.append(received_func_inbox.get())
            print('Received: ', lst, type(lst))
            lst.clear()
        print('*'*50)

        time.sleep(5)


threading.Thread(target=sender1).start()
threading.Thread(target=sender2).start()
threading.Thread(target=received_func).start()
