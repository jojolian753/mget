# -*- coding: utf-8 -*-

import os
import errno

from mmap import mmap


class OverwriteAborted(Exception):
    pass

class saved(object):
    def __init__(self, filename):
        self.fn = filename
        self.ofile = None
        self.fmap = None

        # Check if file exists and if so ask if overwrite necessary.
        prompt = True
        while(prompt):
            if os.access(self.fn, os.O_RDWR):
                u = input("File already exists, overwrite? [y/N] ")
                if u.lower() == 'y':
                    print("Overwriting...")
                    prompt = False
                elif u.lower() == 'n':
                    print("Aborting...")
                    raise OverwriteAborted()

    def __enter__(self):
        # Open and memory map the file.
        self.ofile = open(self.fn, "wb+")
        self.ofile.write(b"\0")

        self.ofile.flush()
        self.fmap = mmap(
            self.ofile.fileno(),
            os.fstat(self.ofile.fileno()).st_size
        )

        return self.fmap

    def __exit__(self, exc_type, exc_value, traceback):
        self.ofile.close()
        self.fmap.close()

with saved("test.txt") as fmap:
    print(fmap)
