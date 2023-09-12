from wenum.externals.reqresp.Response import Response, get_encoding_from_headers


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
        content_encoding = get_encoding_from_headers(dict(self.get_headers()))

        # fallback to default encoding
        if content_encoding is None:
            content_encoding = "utf-8"

        with open(self._body, "rb") as body_file:
            return body_file.read().decode(content_encoding, errors="replace")