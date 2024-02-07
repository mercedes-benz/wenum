from datetime import timedelta, date
from urllib.parse import urljoin

from wenum.externals.moduleman.plugin import moduleman_plugin
from wenum.plugin_api.base import BasePlugin
from wenum.plugin_api.mixins import DiscoveryPluginMixin


@moduleman_plugin
class Logfiles(BasePlugin, DiscoveryPluginMixin):
    name = "logfiles"
    author = ("Ivo Palazzolo (@palaziv)",)
    version = "0.1"
    summary = "Checks for exposed log files."
    description = ("Checks for exposed log files.",)
    category = ["active", "discovery"]
    priority = 99

    parameters = ()

    MAX_DAYS = 10   # determines the date range to generate

    def __init__(self, session):
        BasePlugin.__init__(self, session)

    def validate(self, fuzz_result):
        log_paths = ["log", "logs", "access_log", "access_logs", "error_log", "error_logs", "errorlog", "errorlogs", "accesslog", "accesslogs"]

        return (
                fuzz_result.history.response_redirects_to_directory() and
                fuzz_result.history.urlparse.path.rsplit('/')[-1].lower() in log_paths
        )

    def process(self, fuzz_result):
        self.add_information(f"Log directory found at {fuzz_result.url}. Checking for exposed log files.")

        # check for common log file names first
        common_log_file_names = ["access.log", "error.log", "errors.log", "access.txt", "error.txt", "errors.txt", "errorlog.txt", "accesslog.txt", "errorlog.log", "accesslog.log", "log.txt", "application.log", "debug.log"]
        for log_file_name in common_log_file_names:
            url = urljoin(fuzz_result.url + "/", log_file_name)
            self.queue_url(url)

        # now also check for log files containing dates
        # check for log files from MAX_DAYS ago to today
        end_date = date.today()
        start_date = end_date - timedelta(days=self.MAX_DAYS)

        current_date = start_date
        while current_date < end_date:
            # YYYY-MM-DD.log, YYYY/MM/DD.log, YYYY_MM_DD.log
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y-%m-%d") + ".log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y%m%d") + ".log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y_%m_%d") + ".log")
            self.queue_url(url)

            # YYYY-MM-DD.txt, YYYY/MM/DD.txt, YYYY_MM_DD.txt
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y-%m-%d") + ".txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y%m%d") + ".txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y_%m_%d") + ".txt")
            self.queue_url(url)

            # DD-MM-YYYY.log, DD/MM/YYYY.log, DD_MM_YYYY.log
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d-%m-%Y") + ".log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d%m%Y") + ".log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d_%m_%Y") + ".log")
            self.queue_url(url)

            # DD-MM-YYYY.txt, DD/MM/YYYY.txt, DD_MM_YYYY.txt
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d-%m-%Y") + ".txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d%m%Y") + ".txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d_%m_%Y") + ".txt")
            self.queue_url(url)

            # MM-DD-YYYY.log, MM/DD/YYYY.log, MM_DD_YYYY.log
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m-%d-%Y") + ".log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m%d%Y") + ".log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m_%d_%Y") + ".log")
            self.queue_url(url)

            # MM-DD-YYYY.txt, MM/DD/YYYY.txt, MM_DD_YYYY.txt
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m-%d-%Y") + ".txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m%d%Y") + ".txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m_%d_%Y") + ".txt")
            self.queue_url(url)

            # now do the same as above but append _log to the file name
            # YYYY-MM-DD.log, YYYY/MM/DD.log, YYYY_MM_DD.log
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y-%m-%d") + "_log.log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y%m%d") + "_log.log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y_%m_%d") + "_log.log")
            self.queue_url(url)

            # YYYY-MM-DD.txt, YYYY/MM/DD.txt, YYYY_MM_DD.txt
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y-%m-%d") + "_log.txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y%m%d") + "_log.txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%Y_%m_%d") + "_log.txt")
            self.queue_url(url)

            # DD-MM-YYYY.log, DD/MM/YYYY.log, DD_MM_YYYY.log
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d-%m-%Y") + "_log.log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d%m%Y") + "_log.log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d_%m_%Y") + "_log.log")
            self.queue_url(url)

            # DD-MM-YYYY.txt, DD/MM/YYYY.txt, DD_MM_YYYY.txt
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d-%m-%Y") + "_log.txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d%m%Y") + "_log.txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%d_%m_%Y") + "_log.txt")
            self.queue_url(url)

            # MM-DD-YYYY.log, MM/DD/YYYY.log, MM_DD_YYYY.log
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m-%d-%Y") + "_log.log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m%d%Y") + "_log.log")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m_%d_%Y") + "_log.log")
            self.queue_url(url)

            # MM-DD-YYYY.txt, MM/DD/YYYY.txt, MM_DD_YYYY.txt
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m-%d-%Y") + "_log.txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m%d%Y") + "_log.txt")
            self.queue_url(url)
            url = urljoin(fuzz_result.url + "/", current_date.strftime("%m_%d_%Y") + "_log.txt")
            self.queue_url(url)

            current_date += timedelta(days=1)
