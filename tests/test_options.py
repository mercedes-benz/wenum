import unittest
from wenum.user_opts import Options
import logging
import os
from tomlkit import load
from tomlkit.exceptions import ParseError


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
        options.read_args(parsed_args)
        self._invalid_path(options)

        options.wordlist_list = ["dummy_wordlist.txt"]
        self.assertIsNone(options.basic_validate())

        options.wordlist_list = [f"{os.getcwd()}/dummy_wordlist.txt"]
        self.assertIsNone(options.basic_validate())

        os.chmod("dummy_wordlist.txt", 0o000)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))
        os.chmod("dummy_wordlist.txt", 0o664)

        # Multiple wordlists with one faulty
        options.wordlist_list.append("/qweqwe")
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

    def test_output_access(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_output}", "dummy_output.txt"])
        options.read_args(parsed_args)

        self.assertIsNone(options.basic_validate())

        options.output = "/invalidpath/invalidfile.txtt"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

        options.output = f"{os.getcwd()}/dummy_output.txt"
        self.assertIsNone(options.basic_validate())

        os.chmod("dummy_output.txt", 0o000)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))
        os.chmod("dummy_output.txt", 0o666)

    def test_output_format(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_output}", "dummy_output.txt"])
        options.read_args(parsed_args)

        self.assertEquals("json", options.output_format)

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_output}", "dummy_output.txt",
             f"--{options.opt_name_output_format}", "html"])
        options.read_args(parsed_args)

        self.assertEquals("html", options.output_format)

        options.output_format = "nonexistantformat"

        with self.assertRaises(Exception) as exc:
            options.basic_validate()

    def test_debug_log(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_debug_log}", "dummy_debuglog.txt"])
        options.read_args(parsed_args)

        self.assertIsNone(options.basic_validate())

        options.debug_log = "/invalidpath/invalidfile.txtt"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

        options.debug_log = f"{os.getcwd()}/dummy_debuglog.txt"
        self.assertIsNone(options.basic_validate())

        os.chmod("dummy_debuglog.txt", 0o000)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))
        os.chmod("dummy_debuglog.txt", 0o666)

    def test_dump_config(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_dump_config}", "dummy_config_dump.toml"])
        options.read_args(parsed_args)

        self.assertIsNone(options.basic_validate())

        options.dump_config = "/invalidpath/invalidfile.txtt"
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

        options.dump_config = f"{os.getcwd()}/dummy_config_dump.toml"
        self.assertIsNone(options.basic_validate())

        os.chmod("dummy_config_dump.toml", 0o000)
        with self.assertRaises(Exception) as exc:
            options.basic_validate()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))
        os.chmod("dummy_config_dump.toml", 0o666)

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com/FUZZ/FUZ2Z/FUZ3Z", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt" "dummy_wordlist", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_proxy}", "http://127.0.0.1:8080",
             f"--{options.opt_name_method}", "POST", f"--{options.opt_name_dump_config}", "dummy_config_dump.toml",
             f"--{options.opt_name_data}", "{\"jsontest\":2}", f"--{options.opt_name_header}", "Test: asd", "Testtwo: qweq",
             f"--{options.opt_name_header}", "Test3: qweqwe", f"--{options.opt_name_cookie}", "Cookie=123",
             f"--{options.opt_name_ip}", "127.0.0.1:443", f"--{options.opt_name_iterator}", "product",
             f"--{options.opt_name_threads}", "30", f"--{options.opt_name_sleep}", "2",
             f"--{options.opt_name_plugin_threads}", "4",
             f"--{options.opt_name_location}", f"--{options.opt_name_recursion}", "3",
             f"--{options.opt_name_stop_error}", f"--{options.opt_name_dry_run}",
             f"--{options.opt_name_limit_requests}", "20000", f"--{options.opt_name_request_timeout}", "40",
             f"--{options.opt_name_domain_scope}", f"--{options.opt_name_output}", "dummy_output.txt",
             f"--{options.opt_name_debug_log}", "dummy_debuglog.txt", f"--{options.opt_name_plugins}", "default",
             "robots", f"--{options.opt_name_plugins}", "active", f"--{options.opt_name_colorless}",
             f"--{options.opt_name_quiet}", f"--{options.opt_name_noninteractive}", f"--{options.opt_name_hc}", "200",
             "403", f"--{options.opt_name_hc}", "302", f"--{options.opt_name_filter}", "code=200",
             f"--{options.opt_name_hard_filter}", f"--{options.opt_name_auto_filter}"
             ])
        options.read_args(parsed_args)
        options.export_config()

        with open(options.dump_config, "rb") as file:
            self.assertTrue(load(file))

    def test_config(self):
        self.longMessage = True
        options = Options()
        parser = options.configure_parser()

        # Assert valid toml parses without exception
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
{options.opt_name_wordlist} = ["dummy_wordlist.txt", "dummy_wordlist.txt", "dummy_wordlist.txt"]
{options.opt_name_colorless} = true
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
{options.opt_name_output} = "dummy_output.txt"
{options.opt_name_output_format} = "html"
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
{options.opt_name_threads} = 30
{options.opt_name_plugin_threads} = 4
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_dry_run} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
"""
            file.write(toml_content)

        parsed_args = parser.parse_args(
            [f"--{options.opt_name_url}", "http://example.com", f"--{options.opt_name_wordlist}",
             "dummy_wordlist.txt", f"--{options.opt_name_config}", "dummy_config.toml"])
        self.assertIsNone(options.read_args(parsed_args))

        options.config = "/invalidpath/invalidfile.txtt"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))

        options.config = f"{os.getcwd()}/dummy_config.toml"
        self.assertIsNone(options.import_config())

        os.chmod("dummy_config.toml", 0o000)
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("can not be opened" in str(exc.exception), msg=str(exc.exception))
        os.chmod("dummy_config.toml", 0o666)


        # Assert different kinds of invalid toml throw the right error (faulty datatypes, faulty keys, unknown keys)
        # Assert error on not existing key
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
{options.opt_name_wordlist} = ["dummy_wordlist.txt", "dummy_wordlist.txt", "dummy_wordlist.txt"]
{options.opt_name_colorless} = true
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
{options.opt_name_output} = "dummy_output.txt"
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
{options.opt_name_threads} = 30
{options.opt_name_plugin_threads} = 4
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
# junkline
doesnt_exist = true
"""
            file.write(toml_content)
        options.config = "dummy_config.toml"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("Unknown keys" in str(exc.exception), msg=str(exc.exception))

        # Assert error on invalid TOML
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
# junkline
{options.opt_name_wordlist} = "dummy_wordlist.txt", "dummy_wordlist.txt", "dummy_wordlist.txt"
{options.opt_name_colorless} = true
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
{options.opt_name_output} = "dummy_output.txt"
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
{options.opt_name_threads} = 30
{options.opt_name_plugin_threads} = 4
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
"""
            file.write(toml_content)
        options.config = "dummy_config.toml"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("does not contain valid TOML" in str(exc.exception), msg=str(exc.exception))

        # Assert error on value list type
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
# junkline
{options.opt_name_wordlist} = "dummy_wordlist.txt"
{options.opt_name_colorless} = true
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
{options.opt_name_output} = "dummy_output.txt"
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
{options.opt_name_threads} = 30
{options.opt_name_plugin_threads} = 4
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
"""
            file.write(toml_content)
        options.config = "dummy_config.toml"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("is not a list" in str(exc.exception), msg=str(exc.exception))

        # Assert error on value bool type
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
{options.opt_name_wordlist} = ["dummy_wordlist.txt"]
# junkline
{options.opt_name_colorless} = 2
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
{options.opt_name_output} = "dummy_output.txt"
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
{options.opt_name_threads} = 30
{options.opt_name_plugin_threads} = 4
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
"""
            file.write(toml_content)
        options.config = "dummy_config.toml"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("is not a bool" in str(exc.exception), msg=str(exc.exception))

        # Assert error on value string type
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
{options.opt_name_wordlist} = ["dummy_wordlist.txt"]
{options.opt_name_colorless} = false
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
# junkline
{options.opt_name_output} = 2
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
{options.opt_name_threads} = 30
{options.opt_name_plugin_threads} = 4
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
"""
            file.write(toml_content)
        options.config = "dummy_config.toml"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("is not a string" in str(exc.exception), msg=str(exc.exception))

        # Assert error on value int type
        with open("dummy_config.toml", "w") as file:
            toml_content = f"""
{options.opt_name_url} = "http://example.com/FUZZ/FUZ2Z/FUZ3Z"
{options.opt_name_wordlist} = ["dummy_wordlist.txt"]
{options.opt_name_colorless} = false
{options.opt_name_quiet} = true
{options.opt_name_noninteractive} = true
{options.opt_name_output} = "dummy_output.txt"
{options.opt_name_debug_log} = "dummy_debuglog.txt"
{options.opt_name_proxy} = ["http://127.0.0.1:8080"]
# junkline
{options.opt_name_threads} = true
{options.opt_name_sleep} = 2
{options.opt_name_location} = true
{options.opt_name_recursion} = 3
{options.opt_name_method} = "POST"
{options.opt_name_data} = "{{\\"jsontest\\":2}}"
{options.opt_name_header} = ["Test: asd", "Testtwo: qweq", "Test3: qweqwe"]
{options.opt_name_stop_error} = true
{options.opt_name_hc} = [200, 403, 302]
{options.opt_name_filter} = "code=200"
{options.opt_name_auto_filter} = true
{options.opt_name_hard_filter} = true
{options.opt_name_limit_requests} = 20000
{options.opt_name_ip} = "127.0.0.1:443"
{options.opt_name_request_timeout} = 40
{options.opt_name_domain_scope} = true
{options.opt_name_plugins} = ["default", "robots", "active"]
{options.opt_name_iterator} = "product"
"""
            file.write(toml_content)
        options.config = "dummy_config.toml"
        with self.assertRaises(Exception) as exc:
            options.import_config()
        self.assertTrue("is not an int" in str(exc.exception), msg=str(exc.exception))

    def _invalid_path(self, options):
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

    def test_multiple_wordlists(self):
        pass

    def test_plugin_category(self):
        pass

    def test_plugin_name(self):
        pass

    @classmethod
    def setUpClass(cls) -> None:
        with open("dummy_wordlist.txt", "w") as file:
            file.write("example")

    @classmethod
    def tearDownClass(cls):
        # release resources
        with open("dummy_debuglog.txt", "w") as file:
            file.write("")
        with open("dummy_config.toml", "w") as file:
            file.write("")
        with open("dummy_config_dump.toml", "w") as file:
            file.write("")
        with open("dummy_output.txt", "w") as file:
            file.write("")
        with open("dummy_wordlist.txt", "w") as file:
            file.write("")
