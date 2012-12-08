#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import asyncore
import socket

from time import time
from mmap import mmap


# SEEK_BEG = 0
# SEEK_SET = 1
# SEEK_END = 2


class http_client(asyncore.dispatcher):

    def __init__(self, host, path, parts, pbegin=0, pend=0, m=None):
        asyncore.dispatcher.__init__(self)
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

        # Grab the filename from the end of the URL.
        self.filename = path.split("/")[-1]

        # Check if file exists and if so ask if overwrite necessary.
        if os.access(self.filename, os.O_RDWR) and self.parts > 0:
            u = input("File already exists, overwrite? [y/N] ")
            if u == 'y' or u == 'Y':
                print("Overwriting...")
            else:
                print("Aborting...")
                return None

        # Create a TCP/IP socket and connect to the host with it on port 80.
        print("Connecting...")
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, 80))

        # Parts are greater than 0 so we are the parent, open file, get header.
        if self.parts > 0:
            # Open and memory map the file.
            self.f = open(self.filename, 'wb+')
            self.f.write(b"\0")
            self.f.flush()
            self.m = mmap(self.f.fileno(), os.fstat(self.f.fileno()).st_size)

            # Download the header.
            self.buffer = ("HEAD {0} HTTP/1.1\r\nHost: {1}\r\n\r\n".format(self.path, self.host)).encode("utf-8")
            print("Downloading http://{0}{1}".format(self.host, self.path))

        # Otherwise, we are a child, skip the header and download our segment.
        elif self.parts == 0:
            # Set our own mmap to the one given to us by the parent.
            self.m = m
            # Prepare ourselves to download the segment.
            self.bytes = self.pbegin
            self.length = self.pend
            self.recvhead = 2
            self.buffer = ("GET {0} HTTP/1.1\r\nHost: {1}\r\nRange: bytes={2}-{3}\r\n\r\n".format(self.path, self.host, self.pbegin, self.pend)).encode("utf-8")
            print(self.buffer)

    def handle_connect(self):
        pass

    def handle_read(self):
        # Recieve incoming data.
        data = self.recv(8192)
        # Handle recieving the header, stage 1.
        if self.recvhead == 1:
            self.head = data
            print(self.head)

            # If the file was not found, exit.
            if b"404 Not Found" in data:
                print("404 Not Found")
                self.close()
                self.m.close()
                self.f.close()
                return None

            # Was it found, if not just check if OK.
            if b"302 Found" not in data:
                # If we did not recieve the OK, exit.
                if b"200 OK" not in data:
                    print("Unable to continue download.")
                    self.close()
                    self.m.close()
                    self.f.close()
                    return None

            # If we cannot determine the length of the file, exit.
            if b"Content-Length" not in data:
                print("Cannot determine size.")
                self.close()
                self.m.close()
                self.f.close()
                return None

            # Determine the length of the file.
            line = self.head[self.head.find(b"Content-Length"):]
            line = line[:line.find(b"\r\n")]
            line = line[line.find(b":")+1:]
            self.length = int(line)
            print(self.length)
            self.m.resize(self.length)
            self.recvhead = 2

            # If the number of parts is 1, only get the file.
            if self.parts == 1:
                self.buffer = (
                    "GET {0} HTTP/1.1\r\nHost: {1}\r\n\r\n".format(
                        self.path, self.host
                    )
                ).encode("utf-8")
                print(self.buffer)
                self.pbegin = 0
                self.pend = self.length

            # If the parts is greater than 1, split into segments.
            elif self.parts > 1:
                l = self.length // self.parts
                print("Segment size = {0}".format(l))

                # Download the other segments in separate instances.
                if self.parts == 2:
                    self.h.append(http_client(self.host, self.path, 0, l+1, self.length, self.m))
                if self.parts > 2:
                    for i in range(1, self.parts-1):
                        self.h.append(http_client(self.host, self.path, 0, (i*l)+1, (i+1)*l, self.m))
                    self.h.append(http_client(self.host, self.path, 0, ((i+1)*l)+1, self.length, self.m))

                # Set up the parent download, from beginning of file to segment size.
                self.buffer = ((
                    "GET {0} HTTP/1.1\r\nHost: {1}\r\n"
                    "Range: bytes=0-{2}\r\n\r\n"
                ).format(
                    self.path, self.host, l
                )).encode("utf-8")
                self.length = l
                self.pbegin = 0
                self.pend = self.length
                print(self.buffer)

        # Stage 2, clip the second incoming header and start grabbing the file itself.
        elif self.recvhead == 2:
            # A blank line specifies the end of the header.
            body = data[data.find(b"\r\n\r\n")+4:]

            size = len(body)
            if size > 0:
                # Write what we have to the file.
                self.m[self.bytes:self.bytes+size] = body
                self.bytes += size

                # Keep track of position and inform the user.
                if len(range(size//1024)) == 0:
                    self.ack = size
                else:
                    print("Jet {0}-{1}   {2} of {3} bytes recieved".format(
                        self.pbegin, self.pend, self.bytes, self.length
                    ))

            self.recvhead = 0

        # Just download the rest of the file.
        else:
            size = len(data)
            dataend = self.bytes + size
            self.m[self.bytes:dataend] = data
            self.bytes += size

            # Keep track of position and inform the user.
            if len(range(size//1024)) == 0:
                self.ack += size
            else:
                print("Jet {0}-{1}   {2} of {3} bytes recieved".format(
                    self.pbegin, self.pend, self.bytes, self.length
                ))

            if len(range(self.ack//1024)) > 0:
                print("Jet {0}-{1}   {2} of {3} bytes recieved".format(
                    self.pbegin, self.pend, self.bytes, self.length
                ))
                self.ack -= (1024*len(range(self.ack//1024)))

    # Check to see if the buffer is clear.
    def writable(self):
        return(len(self.buffer) > 0)

    # Handle transmission of the data.
    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    # Handle closing of the connection.
    def handle_close(self):
        self.complete = time()
        if self.bytes > self.length:
            self.bytes = self.bytes-1

        print("Jet {0}-{1}   {2} of {3} bytes recieved".format(
            self.pbegin, self.pend, self.bytes, self.length
        ))
        self.close()


if __name__ == '__main__':
    from urllib.parse import urlparse
    if len(sys.argv) < 2:
        print('usage: {0} host'.format(sys.argv[0]))
    else:
        url = sys.argv[1]
        if "http://" not in url:
            url = "http://{url_address}".format(url_address=url)
        parsed_url = urlparse(url)
        client = http_client(parsed_url.netloc, parsed_url.path, 3)
        asyncore.loop()
        client.m.close()
        client.f.close()
        print("Client jet 1 finished at {0} of {1}".format(
            client.bytes, client.length
        ))
