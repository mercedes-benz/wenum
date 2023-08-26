from typing import Optional
from urllib.parse import urlparse
from urllib.parse import urlunparse

import re

from .Variables import VariablesSet
from .Response import Response

from wenum.helpers.obj_dic import CaseInsensitiveDict

from .TextParser import TextParser


class Request:
    """
    Lower level Request class, though in the long term could be merged with FuzzRequest,
    as Request is only used in the FuzzRequest context
    """
    def __init__(self):
        self.host = None  # www.google.com:80
        self.path = None  # /index.php
        self.params = None  # Mierdaza de index.php;lskjflkasjflkasjfdlkasdf?
        self.schema = "http"  # http

        self.ContentType = (
            "application/x-www-form-urlencoded"  # Default
        )
        self.multiPOSThead = {}

        self.__variablesGET = VariablesSet()
        self._variablesPOST = VariablesSet()
        self._non_parsed_post = None

        # Dict, for example headers["Cookie"]
        self._headers = CaseInsensitiveDict(
            {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1)",
            }
        )

        self.response: Optional[Response] = None  # The response created out of the request

        # ################## lo de debajo no se deberia acceder directamente

        self.time = None  # 23:00:00
        self.ip = None  # 192.168.1.1
        self._method = None
        self.protocol = "HTTP/1.1"  # HTTP/1.1
        self._performHead = ""
        self._performBody = ""

        self._authMethod = None
        self._userpass = ""

        self.description = ""  # For storing information temporarily

        self._timeout = None
        self._totaltimeout = None

        self.totaltime = None
        self.date = None

    @property
    def complete_url(self):
        """
        e.g. http://www.google.es/index.php?a=b
        """
        return urlunparse((self.schema, self.host, self.path,
                           self.params, self.__variablesGET.urlEncoded(), "",))

    @property
    def method(self):
        if self._method is None:
            return "POST" if self._non_parsed_post is not None else "GET"

        return self._method

    @method.setter
    def method(self, value):
        if value == "None":
            value = None

        self._method = value

    @property
    def postdata(self):
        if self.ContentType == "application/x-www-form-urlencoded":
            return self._variablesPOST.urlEncoded()
        elif self.ContentType == "multipart/form-data":
            return self._variablesPOST.multipartEncoded()
        elif self.ContentType == "application/json":
            return self._variablesPOST.json_encoded()
        else:
            return self._variablesPOST.urlEncoded()

    @property
    def url_without_variables(self):
        """
        e.g. http://www.google.es/index.php
        """
        return urlunparse((self.schema, self.host, self.path, "", "", ""))

    @property
    def path_with_variables(self):
        """
        e.g. /index.php?a=b&c=d
        """
        return urlunparse(("", "", self.path, "", self.__variablesGET.urlEncoded(), ""))

    def __str__(self):
        request_string = "[ URL: %s" % self.complete_url
        if self.postdata:
            request_string += ' - {}: "{}"'.format(self.method, self.postdata)
        if "Cookie" in self._headers:
            request_string += ' - COOKIE: "%s"' % self._headers["Cookie"]
        request_string += " ]"
        return request_string

    def set_url(self, urltmp):
        self.__variablesGET = VariablesSet()
        self.schema, self.host, self.path, self.params, variables, f \
            = urlparse(urltmp)
        if "Host" not in self._headers or (not self._headers["Host"]):
            self._headers["Host"] = self.host

        if variables:
            self.__variablesGET.parseUrlEncoded(variables)

    def set_variable_post(self, key, value):
        v = self._variablesPOST.getVariable(key)
        v.update(value)

    def set_variable_get(self, key, value):
        v = self.__variablesGET.getVariable(key)
        v.update(value)

    def get_get_vars(self):
        return self.__variablesGET.variables

    def get_post_vars(self):
        return self._variablesPOST.variables

    def set_post_data(self, pd, boundary=None):
        self._non_parsed_post = pd
        self._variablesPOST = VariablesSet()

        try:
            if self.ContentType == "multipart/form-data":
                self._variablesPOST.parseMultipart(pd, boundary)
            elif self.ContentType == "application/json":
                self._variablesPOST.parse_json_encoded(pd)
            else:
                self._variablesPOST.parseUrlEncoded(pd)
        except Exception:
            try:
                self._variablesPOST.parseUrlEncoded(pd)
            except Exception:
                print("Warning: POST parameters not parsed")
                pass

    ############################################################################

    def add_header(self, key, value):
        self._headers[key] = value

    def __getitem__(self, key):
        if key in self._headers:
            return self._headers[key]
        else:
            return ""

    def get_headers(self):
        header_list = []
        for i, j in self._headers.items():
            header_list += ["%s: %s" % (i, j)]
        return header_list

    # ######## ESTE conjunto de funciones no es necesario para el uso habitual de la clase

    def get_all(self):
        pd = self._non_parsed_post if self._non_parsed_post else ""
        string = (
            str(self.method)
            + " "
            + str(self.path_with_variables)
            + " "
            + str(self.protocol)
            + "\n"
        )
        for i, j in self._headers.items():
            string += i + ": " + j + "\n"
        string += "\n" + pd

        return string

    # #########################################################################

    def header_callback(self, data):
        self._performHead += data

    def body_callback(self, data):
        self._performBody += data

    def substitute(self, src, dst):
        a = self.get_all()
        rx = re.compile(src)
        b = rx.sub(dst, a)
        del rx
        self.parse_request(b, self.schema)

    def parse_request(self, raw_request, prot="http") -> None:
        """
        Receives raw request and sets plenty parameters of Request object instance
        """
        text_parser = TextParser()
        text_parser.set_source("string", raw_request)

        self._variablesPOST = VariablesSet()
        self._headers = {}

        text_parser.read_line()
        try:
            text_parser.search(r"^(\S+) (.*) (HTTP\S*)$")
            self.method = text_parser[0][0]
            self.protocol = text_parser[0][2]
        except Exception as a:
            print(raw_request)
            raise a

        path_tmp = text_parser[0][1].replace(" ", "%20")
        path_tmp = ("", "") + urlparse(path_tmp)[2:]
        path_tmp = urlunparse(path_tmp)

        while True:
            text_parser.read_line()
            if text_parser.search("^([^:]+): (.*)$"):
                self.add_header(text_parser[0][0], text_parser[0][1])
            else:
                break

        self.set_url(prot + "://" + self._headers["Host"] + path_tmp)

        # ignore CRLFs until request line
        while text_parser.lastline == "" and text_parser.read_line():
            pass

        pd = ""
        if text_parser.lastFull_line:
            pd += text_parser.lastFull_line

        while text_parser.read_line():
            pd += text_parser.lastFull_line

        if pd:
            boundary = None
            if "Content-Type" in self._headers:
                values = self._headers["Content-Type"].split(";")
                self.ContentType = values[0].strip().lower()
                if self.ContentType == "multipart/form-data":
                    boundary = values[1].split("=")[1].strip()

            self.set_post_data(pd, boundary)
