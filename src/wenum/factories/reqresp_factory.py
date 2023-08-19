import pycurl

from ..helpers.str_func import convert_to_unicode
from ..externals.reqresp import Response


class ReqRespRequestFactory:

    @staticmethod
    def to_http_object(fuzz_request, pycurl_c) -> pycurl.Curl:
        pycurl_c.setopt(pycurl.MAXREDIRS, 5)

        pycurl_c.setopt(pycurl.WRITEFUNCTION, fuzz_request._request.body_callback)
        pycurl_c.setopt(pycurl.HEADERFUNCTION, fuzz_request._request.header_callback)

        pycurl_c.setopt(pycurl.NOSIGNAL, 1)
        pycurl_c.setopt(pycurl.SSL_VERIFYPEER, False)
        pycurl_c.setopt(pycurl.SSL_VERIFYHOST, 0)

        pycurl_c.setopt(pycurl.PATH_AS_IS, 1)

        pycurl_c.setopt(
            pycurl.URL, convert_to_unicode(fuzz_request._request.complete_url)
        )

        authMethod, userpass = fuzz_request._request.get_auth()
        if authMethod or userpass:
            if authMethod == "basic":
                pycurl_c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
            elif authMethod == "ntlm":
                pycurl_c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_NTLM)
            elif authMethod == "digest":
                pycurl_c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
            pycurl_c.setopt(pycurl.USERPWD, convert_to_unicode(userpass))
        else:
            pycurl_c.unsetopt(pycurl.USERPWD)

        pycurl_c.setopt(
            pycurl.HTTPHEADER, convert_to_unicode(fuzz_request._request.get_headers())
        )

        curl_options = {
            "GET": pycurl.HTTPGET,
            "POST": pycurl.POST,
            "PATCH": pycurl.UPLOAD,
            "HEAD": pycurl.NOBODY,
        }

        for verb in curl_options.values():
            pycurl_c.setopt(verb, False)

        if fuzz_request._request.method in curl_options:
            pycurl_c.unsetopt(pycurl.CUSTOMREQUEST)
            pycurl_c.setopt(curl_options[fuzz_request._request.method], True)
        else:
            pycurl_c.setopt(pycurl.CUSTOMREQUEST, fuzz_request._request.method)

        if fuzz_request._request._non_parsed_post is not None:
            pycurl_c.setopt(
                pycurl.POSTFIELDS,
                convert_to_unicode(fuzz_request._request._non_parsed_post),
            )

        # We do not want pycurl to automatically follow requests. We wouldn't be able to parse
        # The requests inbetween in a modular way
        pycurl_c.setopt(pycurl.FOLLOWLOCATION, 0)

        if fuzz_request.wf_ip:
            pycurl_c.setopt(
                pycurl.CONNECT_TO,
                ["::{}:{}".format(fuzz_request.wf_ip["ip"], fuzz_request.wf_ip["port"])],
            )

        return pycurl_c

    @staticmethod
    def from_http_object(fuzz_request, pycurl_c: pycurl.Curl, header, body):
        raw_header = header.decode("utf-8", errors="surrogateescape")

        fuzz_request._request.totaltime = pycurl_c.getinfo(pycurl.TOTAL_TIME)

        fuzz_request._request.response = Response()
        fuzz_request._request.response.parse_response(raw_header, rawbody=body)

        return fuzz_request._request.response
