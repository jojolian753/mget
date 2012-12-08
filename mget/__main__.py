# -*- coding: utf-8 -*-
"""
mget.__main__
~~~~~~~~~~~~~

Main package executable entry point.
"""

from urllib.parse import urlparse

from .http.client import HTTP_client


# TODO(placidrage):
# - add proper argument parsing with argparse.
# - move urlparsing to mget.client.

if len(sys.argv) < 2:
    print('usage: {0} host'.format(sys.argv[0]))
else:
    url = sys.argv[1]
    if "http://" not in url:
        url = "http://{url_address}".format(url_address=url)
    parsed_url = urlparse(url)
    client = HTTP_client(parsed_url.netloc, parsed_url.path, 3)
    asyncore.loop()
    client.m.close()
    client.f.close()
    print("Client jet 1 finished at {0} of {1}".format(
        client.bytes, client.length
    ))
