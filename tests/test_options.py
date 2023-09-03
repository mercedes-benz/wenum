import unittest
from wenum.user_opts import Options
import logging


class OptionsTest(unittest.TestCase):
    def test_ip_option(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()
        parsed_args = parser.parse_args(["--ip", "127.0.0.1:80"])
        options.read_args(parsed_args)
        self.assertEqual(options.ip, "127.0.0.1:80", msg=f"qwe")

        parsed_args = parser.parse_args([f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}", "example_wordlist.txt", f"--{options.opt_name_ip}", "127.0.0w.1:443"])
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("Please ensure that the IP address" in str(exc.exception), msg=str(exc.exception))

        parsed_args = parser.parse_args([f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}", "example_wordlist.txt", f"--{options.opt_name_ip}", "127.0.0.1:"])
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("Please ensure that the port of" in str(exc.exception), msg=str(exc.exception))

        parsed_args = parser.parse_args([f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}", "example_wordlist.txt", f"--{options.opt_name_ip}", "127.0.0.1:w"])
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("Please ensure that the port of" in str(exc.exception), msg=str(exc.exception))

        parsed_args = parser.parse_args([f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}", "example_wordlist.txt", f"--{options.opt_name_ip}", "127.0.0.1:80:32"])
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("contains one colon" in str(exc.exception), msg=str(exc.exception))

        parsed_args = parser.parse_args([f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}", "example_wordlist.txt", f"--{options.opt_name_ip}", "127.0.0.1"])
        options.read_args(parsed_args)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("contains one colon" in str(exc.exception), msg=str(exc.exception))

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
