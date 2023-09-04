import unittest
from wenum.user_opts import Options
import logging
import os


class OptionsTest(unittest.TestCase):
    def test_ip_option(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_ip}", "127.0.0w.1:443"])
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("Please ensure that the IP address" in str(exc.exception), msg=str(exc.exception))

        options.ip = "127.0.0.1:"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("Please ensure that the port of" in str(exc.exception), msg=str(exc.exception))

        options.ip = "127.0.0.1:w"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("Please ensure that the port of" in str(exc.exception), msg=str(exc.exception))

        options.ip = "127.0.0.1:80:32"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("contains one colon" in str(exc.exception), msg=str(exc.exception))

        options.ip = "127.0.0.1"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("contains one colon" in str(exc.exception), msg=str(exc.exception))

    def test_wordlist_access(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "this_doesnt_exist.txt"])
        self._invalid_path(options, parsed_args)

        options.wordlist_list = ["dummy_wordlist.txt"]
        self.assertIsNone(options.basic_validate())

        options.wordlist_list = [f"{os.getcwd()}/dummy_wordlist.txt"]
        self.assertIsNone(options.basic_validate())

        os.chmod("dummy_wordlist.txt", 0o000)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))
        os.chmod("dummy_wordlist.txt", 0o444)

        # Multiple wordlists with one faulty
        options.wordlist_list.append("/qweqwe")
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

        # TODO output, debuglog, dumpconfig, config

    def test_output_access(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_output}", "dummy_wordlist.txt"])
        options.read_args(parsed_args)

        self.assertIsNone(options.basic_validate())

        options.output = "/qweqwe"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))


    def _invalid_path(self, options, parsed_args):
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

    def test_colorless(self):
        # Init Term and ensure that ANSII color codes are never used
        pass

    def test_proxy(self):
        # Ensure requests are sent to the proxy + several proxies mean split up connections. Mock local proxy for that
        pass

    def test_method(self):
        # Ensure that the method changes, + combined with --data
        pass

    def test_header(self):
        # Ensure that headers are being set in the request
        pass

    def test_domain_scope(self):
        # Ensure scope check is IP by default and triggers on domain change if activated
        pass

    def test_import(self):
        pass

    def test_export(self):
        pass

    def test_multiple_wordlists(self):
        pass

    def test_plugin_category(self):
        pass

    def test_plugin_name(self):
        pass
