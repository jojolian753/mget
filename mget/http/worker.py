# -*- coding: utf-8 -*-
"""
mget.http.worker
~~~~~~~~~~~~~~~~

http async workers that given a range, download parts of a file.
"""

import asyncore
import socket


class Worker(asyncore.dispatcher):
    """
    Async http worker class.
    """

    def __init__(self, host, path, parts, mmapf, pbegin=0, pend=0):
        super(Worker, self).__init__()
        # Initialize class member variables.
        self.done = 0
        self.h = [self]
        self.recvhead = 1
        self.bytes = 0
        self.ack = 0
        self.begin = time()
        self.path = path
        self.parts = parts
        self.host = host
        self.buffer = ""
        self.pbegin = pbegin
        self.pend = pend
        self.length = 8192
        self.f = None

        # Create a TCP/IP socket and connect to the host with it on port 80.
        print("Connecting...")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, 80))

        # Set our own mmap to the one given to us by the parent.
        self.m = m
        # Prepare ourselves to download the segment.
        self.bytes = self.pbegin
        self.length = self.pend
        self.recvhead = 2
        self.buffer = ((
            "GET {0} HTTP/1.1\r\nHost: {1}\r\n"
            "Range: bytes={2}-{3}\r\n\r\n"
        ).format(
            self.path, self.host, self.pbegin, self.pend
        )).encode("utf-8")
        print(self.buffer)

    # -------------------------------------------------------------------------

    # Check to see if the buffer is clear.
    def writable(self):
        return(len(self.buffer) > 0)

    # -------------------------------------------------------------------------

    # Handle transmission of the data.
    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    # -------------------------------------------------------------------------

    # Handle closing of the connection.
    def handle_close(self):
        self.complete = time()
        if self.bytes > self.length:
            self.bytes = self.bytes-1

        print("Jet {0}-{1}   {2} of {3} bytes recieved".format(
            self.pbegin, self.pend, self.bytes, self.length
        ))
        self.close()

# -----------------------------------------------------------------------------
