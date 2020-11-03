import logging
import os
from typing import List
from log import *
from frame import Frame, parse_ack_index, to_ack_bytes
from frame import sequence_m
from medium import Medium

import _thread

import time


# powered by HAPPY

class Sender:
    window_size: int
    window_left: int
    window_current: int
    window_max: int
    buffer: List[bytes]
    medium: Medium
    timeout: int

    is_timer_running = False

    def frame_timer(self, index: int, delay):
        delay_base = 0.1
        delay_cnt = int(delay / delay_base)
        cur_delay = 0
        while cur_delay < delay_cnt:
            if not self.is_timer_running:
                return
            time.sleep(delay)
            cur_delay += 1
        if self.is_timer_running:
            info("time out!")
            self.on_timeout()

    def __init__(self, timeout):
        self.window_size = 2 ** sequence_m - 1
        self.window_left = 0
        self.window_current = self.window_left
        self.window_max = (self.window_left + self.window_size) % (self.window_size + 1)  # forbid index
        self.buffer = [b'' for i in range(self.window_size)]
        self.timeout = timeout
        self.status_dict = {i: False for i in range(self.window_size)}
        self.medium = None

    def set_medium(self, medium):
        self.medium = medium

    def slide_window_to_next(self):
        # print(f"left from: {self.window_left}")
        self.window_left = (1 + self.window_left) % (self.window_size)
        # print(f"left now: {self.window_left}")
        self.window_max = (self.window_left + self.window_size) % (self.window_size)  # forbid index

    def slide_window_current(self):
        self.window_current = (1 + self.window_current) % (self.window_size)

    def send_message(self, data, ):
        # logger.debug(f"call send message with current {self.window_current}")
        if self.window_current == self.window_max:
            return -1  # full
        msg_frame = Frame(b'', delay_cast=True)
        msg_frame.index = self.window_current
        msg_frame.data = data
        frame_bytes = msg_frame.pack_to_frame()
        status(f"send data {data}")
        self.medium.send_bytes(frame_bytes)

        # restore
        self.buffer[self.window_current] = frame_bytes

        self.status_dict[self.window_current] = False

        self.slide_window_current()

        info(f"window sf at {self.window_left}")
        # start timer
        self.is_timer_running = True
        _thread.start_new_thread(self.frame_timer, (self.window_current, self.timeout))
        return 0

    def on_ack_receive(self, frame_bytes):
        ack_index:int = parse_ack_index(frame_bytes)
        success(f"on ack receive {ack_index}, Sf {self.window_left},  Sn {self.window_current}")

        if ack_index == -1:
            return
        right_ack_index = False
        i = self.window_left
        while i != self.window_current:
            if i == ack_index:
                right_ack_index = True
            i += 1
        if self.window_current == ack_index:
            right_ack_index = True
        if right_ack_index:
            # if self.window_left <= ack_index <= self.window_current:

            self.status_dict[ack_index] = True

            # while ack_index != self.window_current:
            while ack_index != self.window_left:
                # self.status_dict[ack_index] = True
                # self.buffer[ack_index] = b''
                ack_index += 1
            self.slide_window_to_next()
            status(f"status: sf:{self.window_left} sn:{self.window_current}")
            self.is_timer_running = False
        else:
            status(f"wrong ack, index left {self.window_left}, ack_index {ack_index}, Sn {self.window_current}")

    def on_timeout(self):
        if not self.is_timer_running:
            return
        index = self.window_left

        self.is_timer_running = True
        _thread.start_new_thread(self.frame_timer, (self.window_current, self.timeout))

        status(f"restore at Sf: {index}, Sn:{self.window_current}")
        while index != self.window_current:
            frame_bytes = self.buffer[index]
            self.status_dict[self.window_current] = False
            self.medium.send_bytes(frame_bytes)
            index = (index + 1) % (self.window_size + 1)


try:
    sender = Sender(timeout=1)
    medium = Medium(emulate_wrong_frame_fact=0.1)
    medium.set_role(sender)
    medium.sender.set_medium(medium=medium)

    medium.run()

    with open("to_send.txt", 'rb') as f:
        message_list = f.read().split(b'\n')

    for message in message_list:
        while True:
            status_code = medium.sender.send_message(message)
            if status_code == -1:
                time.sleep(1)
            else:
                break

    success("finish all task.")
    input()
    # input("press any key to exit\n")
except Exception:
    os._exit(1)
