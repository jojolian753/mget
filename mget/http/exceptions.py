# -*- coding: utf-8 -*-

from http.client import responses


class HTTPResponseError(EnvironmentError):
    def __init__(self, response_code, filename):
        super(HTTPResponseError, self).__init(
            (response_code, responses[response_code], filename)
        )
