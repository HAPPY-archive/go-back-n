import _thread
import os
import socket
import time
import random

import frame
from log import *


# powered by HAPPY

class Medium:
    as_sender: bool
    host = "127.0.0.1"
    port = 6666
    s: socket
    conn: socket
    addr: object
    fixed_transmitter_size = 50
    should_emulate_timeout = False
    should_terminate = False
    ack_fail_probably_fact = 0.5
    emulate_wrong_frame_fact = 0

    def __init__(self, as_sender=True, should_emulate_timeout=False, emulate_timeout_fact=0.5,
                 emulate_wrong_frame_fact=0):
        self.as_sender = as_sender
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ack_fail_probably_fact = emulate_timeout_fact
        self.emulate_wrong_frame_fact = emulate_wrong_frame_fact
        if as_sender:
            self.s.connect((self.host, self.port))
            success(f"connected to {self.host}:{self.port}")
            # self.conn = self.s
            # s.send(b"Hello Server")

        else:
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.host, self.port))
            self.s.listen(5)
            success(f"listening on {self.host}:{self.port}")

        self.should_emulate_timeout = should_emulate_timeout

    def set_role(self, role):
        if self.as_sender:
            self.sender = role
        else:
            self.receiver = role

    def handle_receiver(self, data: bytes):
        if self.receiver is not None:
            self.received = True
            self.receiver.on_message_arrive(data)
        else:
            print("fail to find receiver")

    def listener(self):
        while not self.should_terminate:
            # print("listening...")
            data: bytes = self.conn.recv(self.fixed_transmitter_size)
            # print(f"listened {data}")
            self.handle_receiver(data)
            # _thread.start_new_thread(self.handle_receiver, (data,))

    def handle_sender(self, data: bytes):
        # if data.startswith(b"ack"):
        # print(f"sender receive {data} ack")
        self.sender.on_ack_receive(data)

    def active_listener(self):
        # both ack and message frame for sender
        try:
            while 1:
                # print("recving ...")
                # time.sleep(1)
                data: bytes = self.s.recv(self.fixed_transmitter_size)
                _thread.start_new_thread(self.handle_sender, (data,))
                # print(f"recved data ... {data}")
                self.handle_sender(data)
        except Exception:
            success("see you.")
            os._exit(1)

    def timeout_routine(self):
        while True:
            time.sleep(5)
            if self.received:
                self.received = False
            else:
                self.receiver.write_buffer_to_file()
                self.should_terminate = True
                try:
                    self.conn.close()
                finally:
                    exit(0)

    def run(self):
        if self.as_sender:
            status("sender medium preparing...")
            # self.active_listener()
            _thread.start_new_thread(self.active_listener, ())
            # print("sender medium exit.")

        else:
            status("receiver medium listening...")
            self.conn, self.addr = self.s.accept()
            _thread.start_new_thread(self.timeout_routine, ())
            self.listener()
            self.received = False
            input("press any key to exit\n")

            # input()

    def send_ack(self, data: bytes):
        status(f"send ack {frame.parse_ack_index(data)}")
        if self.should_emulate_timeout:
            if random.random() < self.ack_fail_probably_fact:
                status("emulate ack frame lost, don't send ack frame here.")
                return
        self.conn.send(data.ljust(self.fixed_transmitter_size, b'\x00'))
        # print("send ack finish")

    def receive_ack(self):
        pass

    def send_bytes(self, data: bytes):
        time.sleep(1)

        if random.random() < self.emulate_wrong_frame_fact:
            status("emulate damage frame here.")
            data = data[:random.randint(1, len(data))]
        data = data.ljust(self.fixed_transmitter_size, b'\x00')

        # print(f"send {data}")
        self.s.send(data)
        pass
