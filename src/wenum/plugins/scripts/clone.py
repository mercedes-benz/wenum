import itertools
import os
from urllib.parse import urlparse

from wenum.plugin_api.base import BasePlugin
from wenum.externals.moduleman.plugin import moduleman_plugin
import string


@moduleman_plugin
class Clone(BasePlugin):
    name = "clone"
    author = ("MTD",)
    version = "0.1"
    summary = "Save obtained content to disk."
    description = ("Save obtained content to disk. The headers and contents will be split and "
                   "saved in separate dirs for easier post processing purposes",)
    category = ["active", "discovery"]
    priority = 99
    headers_folder = "headers"
    content_folder = "content"

    parameters = (
    )

    def __init__(self, session):
        BasePlugin.__init__(self, session)
        self.safe_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits + '._/'
        if session.options.output:
            output_dir = f"{session.options.output}_{self.name}"
            os.makedirs(output_dir, exist_ok=True)
            self.output_dir = output_dir
        else:
            self.disabled = True

    def validate(self, fuzz_result):
        if fuzz_result.code != 404:
            return True
        return False

    def process(self, fuzz_result):
        # e.g. http://example.com/admin/login.php -> admin/login.php
        requested_path = f"{urlparse(fuzz_result.url).path.lstrip('/')}"
        # Sanitize the path
        requested_path = ''.join([c for c in requested_path if c in self.safe_chars])

        # Magic taken from
        # https://stackoverflow.com/questions/49695477/removing-specific-duplicated-characters-from-a-string-in-python
        # Strips repeated slashes within the path.
        requested_path = "".join(k if k in "/" else "".join(v) for k, v in
                                 itertools.groupby(requested_path, lambda c: c))

        # If it is the base of the dir, e.g. /admin/, add an artificial file name
        if requested_path.endswith('/') or requested_path == '':
            requested_path += 'f_index_wenum_created'
        else:
            filename = os.path.basename(requested_path)
            new_filename = f"f_{filename}"
            # Replace the filename with the new_filename
            requested_path = requested_path[:-len(filename)] + new_filename

        # Split the path. If the path was "admin/login.php", it will be ["admin", "login.php"],
        # and temp_path_list will be of length 2. Meaning login.php is the file f_login.php, and the entries
        # before are the dirs with d_admin
        temp_path_list = requested_path.split('/')
        if len(temp_path_list) > 1:
            first_index = 0
            for i in range(len(temp_path_list) - 1):
                temp_path_list[first_index + i] = f"d_{temp_path_list[first_index + i]}"
            requested_path = '/'.join(temp_path_list)

        # create separate paths for header file and content file to be written
        # prepend protocol/scheme as dir
        output_path_headers = os.path.join(self.output_dir,
                                           f"{fuzz_result.history.scheme}/{self.headers_folder}/{requested_path}")
        output_path_content = os.path.join(self.output_dir,
                                           f"{fuzz_result.history.scheme}/{self.content_folder}/{requested_path}")

        # If any of the final output paths is outside the root output dir,
        # something unwanted has happened during parsing.
        # Do not save the file, simply return for safety purposes.
        if not os.path.realpath(output_path_headers).startswith(os.path.realpath(self.output_dir)) \
                or not os.path.realpath(output_path_content).startswith(os.path.realpath(self.output_dir)):
            self.add_exception_information(f"{output_path_headers} or {output_path_content} "
                                           f"is outside the root write directory.")
            return

        # Join response headers
        headers_joined = ""
        for item in fuzz_result.history._request.response._headers:
            headers_joined += f"{item[0]}:{item[1]}\n"
        headers_joined += "\n"

        # Create dir path and save headers and content
        os.makedirs(os.path.dirname(output_path_headers), exist_ok=True)
        with open(output_path_headers, "w") as f:
            f.write(headers_joined)

        os.makedirs(os.path.dirname(output_path_content), exist_ok=True)
        with open(output_path_content, "w") as f:
            f.write(fuzz_result.content)
