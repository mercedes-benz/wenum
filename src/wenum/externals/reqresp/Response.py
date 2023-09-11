import re
import cgi

from io import BytesIO
import gzip
import zlib

from .TextParser import TextParser


def get_encoding_from_headers(headers):
    """Returns encodings from given HTTP Header Dict.

    :param headers: dictionary to extract encoding from.
    :rtype: str
    """

    content_type = headers.get("Content-Type")

    if not content_type:
        return None

    content_type, params = cgi.parse_header(content_type)

    if "charset" in params:
        return params["charset"].strip("'\"")

    if "text" in content_type:
        return "ISO-8859-1"

    if "image" in content_type:
        return "utf-8"

    if "application/json" in content_type:
        return "utf-8"


def get_encodings_from_content(content):
    """Returns encodings from given content string.

    :param content: bytestring to extract encodings from.
    """
    charset_re = re.compile(r'<meta.*?charset=["\']*(.+?)["\'>]', flags=re.I)
    pragma_re = re.compile(r'<meta.*?content=["\']*;?charset=(.+?)["\'>]', flags=re.I)
    xml_re = re.compile(r'^<\?xml.*?encoding=["\']*(.+?)["\'>]')

    return (
        charset_re.findall(content)
        + pragma_re.findall(content)
        + xml_re.findall(content)
    )


class Response:
    def __init__(self, protocol="", code="", message=""):
        self.protocol = protocol  # HTTP/1.1
        self.code = code  # 200
        self.message = message  # OK
        self._headers = []  # well then the headers are the same as in the request
        self.__content = (
            ""  # content of the response (only if Content-Length exists)
        )
        self.md5 = ""  # hash of the result contents
        self.charlen = ""  # Number of characters in the response

    def add_header(self, key, value):
        self._headers += [(key, value)]

    def del_header(self, key):
        for i in self._headers:
            if i[0].lower() == key.lower():
                self._headers.remove(i)

    def add_content(self, text):
        self.__content = self.__content + text

    def __getitem__(self, key):
        for i, j in self._headers:
            if key == i:
                return j
        print("Error al obtener header!!!")

    def get_cookie(self):
        str = []
        for i, j in self._headers:
            if i.lower() == "set-cookie":
                str.append(j.split(";")[0])
        return "; ".join(str)

    def has_header(self, key):
        for i, j in self._headers:
            if i.lower() == key.lower():
                return True
        return False

    def get_location(self):
        for i, j in self._headers:
            if i.lower() == "location":
                return j
        return None

    def header_equal(self, header, value):
        for i, j in self._headers:
            if i == header and j.lower() == value.lower():
                return True
        return False

    def get_headers(self):
        return self._headers

    def get_content(self):
        return self.__content

    def get_text_headers(self):
        string = (
            str(self.protocol) + " " + str(self.code) + " " + str(self.message) + "\r\n"
        )
        for i, j in self._headers:
            string += i + ": " + j + "\r\n"

        return string

    def get_all(self):
        string = self.get_text_headers() + "\r\n" + self.get_content()
        return string

    def substitute(self, src, dst):
        a = self.get_all()
        b = a.replace(src, dst)
        self.parse_response(b)

    def get_all_wpost(self):
        string = (
            str(self.protocol) + " " + str(self.code) + " " + str(self.message) + "\r\n"
        )
        for i, j in self._headers:
            string += i + ": " + j + "\r\n"
        return string

    def parse_response(self, rawheader, rawbody=None):
        self.__content = ""
        self._headers = []

        text_parser: TextParser = TextParser()
        text_parser.set_source("string", rawheader)

        text_parser.read_until(r"(HTTP/[0-9.]+) ([0-9]+)")
        while True:
            while True:
                try:
                    self.protocol = text_parser[0][0]
                except Exception:
                    self.protocol = "unknown"

                try:
                    self.code = text_parser[0][1]
                except Exception:
                    self.code = "0"

                if self.code != "100":
                    break
                else:
                    text_parser.read_until(r"(HTTP/[0-9.]+) ([0-9]+)")

            self.code = int(self.code)

            while True:
                text_parser.read_line()
                if text_parser.search("^([^:]+): ?(.*)$"):
                    self.add_header(text_parser[0][0], text_parser[0][1])
                else:
                    break

            # curl sometimes sends two headers when using follow, 302 and the final header
            # also when using proxies
            text_parser.read_line()
            if not text_parser.search(r"(HTTP/[0-9.]+) ([0-9]+)"):
                break
            else:
                self._headers = []

        # ignore CRLFs until request line
        while text_parser.lastline == "" and text_parser.read_line():
            pass

        # TODO: this should be added to rawbody not directly to __content
        if text_parser.lastFull_line:
            self.add_content(text_parser.lastFull_line)

        while text_parser.skip(1):
            self.add_content(text_parser.lastFull_line)

        self.del_header("Transfer-Encoding")

        if self.header_equal("Transfer-Encoding", "chunked"):
            result = ""
            content = BytesIO(rawbody)
            hexa = content.readline()
            nchunk = int(hexa.strip(), 16)

            while nchunk:
                result += content.read(nchunk)
                content.readline()
                hexa = content.readline()
                nchunk = int(hexa.strip(), 16)

            rawbody = result

        if self.header_equal("Content-Encoding", "gzip"):
            compressedstream = BytesIO(rawbody)
            gzipper = gzip.GzipFile(fileobj=compressedstream)
            rawbody = gzipper.read()
            self.del_header("Content-Encoding")
        elif self.header_equal("Content-Encoding", "deflate"):
            try:
                deflater = zlib.decompressobj()
                deflated_data = deflater.decompress(rawbody)
                deflated_data += deflater.flush()
            except zlib.error:
                try:
                    deflater = zlib.decompressobj(-zlib.MAX_WBITS)
                    deflated_data = deflater.decompress(rawbody)
                    deflated_data += deflater.flush()
                except zlib.error:
                    deflated_data = ""
            rawbody = deflated_data
            self.del_header("Content-Encoding")

        if rawbody is not None:
            # Try to get charset encoding from headers
            content_encoding = get_encoding_from_headers(dict(self.get_headers()))

            # fallback to default encoding
            if content_encoding is None:
                content_encoding = "utf-8"

            self.__content = rawbody.decode(content_encoding, errors="replace")
