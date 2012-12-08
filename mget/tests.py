#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class Session(object):
    def __init__(self, filename):
        print("initialization")
        self.filename = filename
    def __enter__(self):
        try:
            raise Exception
        except Exception:
            print("caught exception")
        print("enter")
        return self.filename
    def __exit__(self, exc_type, exc_value, traceback):
        print("exit")


with Session("test") as exc:
    try:
        raise Exception
    except Exception:
        print("caught exception")
    print("CM code block.")
    print(exc)
