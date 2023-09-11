from wenum.externals.reqresp import Response


class CachedResponse(Response):
    def __init__(self, protocol="", code="", body=None, header=None, length=None):
        super().__init__(protocol, code, "")
        self._body = body
        if header is not None and header != '':
            self.parse_response(header)
        else:
            self.protocol = "HTTP/1.1"
            self.code = code
            self.charlen = length

    def get_content(self):
        if self._body is None:
            return super().get_content()
        with open(self._body, "rb") as body_file:
            return body_file.read()