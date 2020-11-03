import os
import sys
import time
from log import *
from frame import Frame, to_ack_bytes, sequence_m
from medium import Medium


# powered by HAPPY

class Receiver:
    expected_index: int
    buffer: bytes
    medium: Medium
    sender_window_size: int
    received = False
    max_timeout: int
    filename: str

    def __init__(self, medium: Medium, output_filename, max_timeout=20):
        self.medium = medium
        self.expected_index = 0
        self.max_index_mod = 2 ** sequence_m - 1
        self.buffer = b''
        self.max_timeout = max_timeout
        self.filename = output_filename

    def on_message_arrive(self, message: bytes, ):
        frame = Frame(message)
        if frame.is_corrupt:
            # warning(f"corrupt frame {frame}")
            warning(f"corrupt frame received.")
            return
        if frame.index == self.expected_index:
            self.buffer = self.buffer + frame.data
            success(f"receive : {frame.data}")
            self.medium.send_ack(to_ack_bytes(self.expected_index))  # self.expected_index
            self.expected_index = (1 + self.expected_index) % self.max_index_mod
            print(f"expected next :{self.expected_index}")
            received = True
        else:
            warning(f"unexpected frame index: {frame.index}, expect {self.expected_index}")

    def write_buffer_to_file(self):
        with open(self.filename, 'wb') as f:
            f.write(self.buffer)
        success(f"writing to {self.filename} with {self.buffer} successfully after TIMEOUT")
        status("see you.")
        os._exit(1)
        # exit(0)

    def timeout_routine(self):
        while True:
            time.sleep(self.max_timeout)
            if self.received:
                self.received = False
                continue
            else:
                self.write_buffer_to_file()


try:
    status("start")

    medium = Medium(as_sender=False, should_emulate_timeout=True, emulate_timeout_fact=0.1,  max_timeout=10)
    receiver = Receiver(medium, "received_result.txt")
    receiver.medium.set_role(receiver)
    receiver.medium.run()
except Exception:
    os._exit(1)
