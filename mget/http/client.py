# -*- coding: utf-8 -*-

import posixpath

# -----------------------------------------------------------------------------

class Client(object):
    """
    HTTP downloading management wrapper class
    Spawns async workers to download parts of a multi-part download job.
    """
    # -------------------------------------------------------------------------

    def __init__(self, host, path, parts, pbegin=0, pend=0, m=None):
        super(Client, self).__init__()

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
        self.filename = posixpath.basename(path)
        print(self.filename)

        # Check if file exists and if so ask if overwrite necessary.
        if self.parts > 0:
            # Download the header.
            self.buffer = ((
                "HEAD {0} HTTP/1.1\r\n"
                "Host: {1}\r\n\r\n"
            ).format(
                self.path, self.host
            )).encode("utf-8")

            print("Downloading http://{0}{1}".format(self.host, self.path))

    # -------------------------------------------------------------------------

    def handle_connect(self):
        pass

    # -------------------------------------------------------------------------

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

# -----------------------------------------------------------------------------
