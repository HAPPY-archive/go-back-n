import struct

import binascii

sequence_m = 4


def parse_ack_index(message: bytes) -> int:
    if message[:3] != b"ack" or len(message) < 7:
        return -1
    return struct.unpack('I', message[3:7])[0]


def to_ack_bytes(index)->bytes:
    return b"ack" + struct.pack('I', index)


class Frame:
    index: int
    data: bytes
    length: int
    m: int  # size of index
    is_corrupt = False

    # struct:
    # index . data length . data . crc
    def __init__(self, frame_bytes: bytes, delay_cast=False, m=sequence_m):
        self.m = m
        assert 2 ** self.m < 256 ** 4
        if not delay_cast:
            self.cast_from_bytes(frame_bytes)

    def cast_from_bytes(self, frame_bytes: bytes):
        assert len(frame_bytes) > 4
        self.index = struct.unpack('I', frame_bytes[:4])[0]
        self.length = struct.unpack('I', frame_bytes[4:8])[0]
        if self.length + 8 > len(frame_bytes):
            self.is_corrupt = True
        self.data = frame_bytes[8:8 + self.length]
        crc = struct.unpack('I', frame_bytes[8 + self.length:8 + self.length + 4])[0]
        if not self.verify_crc(self.data, crc):
            self.is_corrupt = True

    @staticmethod
    def calculate_crc(data):
        return binascii.crc32(data)

    @staticmethod
    def verify_crc(data: bytes, crc_result: int):
        return crc_result == binascii.crc32(data)

    def pack_to_frame(self):
        assert self.index < 2 ** self.m - 1
        return struct.pack('I', self.index) + struct.pack('I', len(self.data)) + self.data + \
               struct.pack('I', self.calculate_crc(self.data))
