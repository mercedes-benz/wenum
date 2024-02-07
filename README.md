# wenum

A wfuzz fork

We have taken the tool wfuzz as a base and gave it a little twist in its direction. 
We want to ease the process of mapping a web application's directory structure, and not spend too much attention on anything else (e.g. determining vulnerable states). 
The focus is therefore different, and unfortunately, some features will even be removed. 
That may be due to a feature clashing with the intended direction of wenum (e.g. the AllVarQueue), or simply because there are convenience features that we think are not important enough to maintain (e.g. manipulating the wordlist entries on the tool startup).

Maintained for Debian 10 and Kali, Python3.10+

## Usage
```
wenum --help

usage: wenum [-h] [-c] [-q] [-n] [-v] [-w [WORDLIST ...]] [-o OUTPUT] [-f {json,html,all}] [-l DEBUG_LOG] [--dump-config DUMP_CONFIG] [-K CONFIG] [--plugins [PLUGINS ...]] [--cache-dir CACHE_DIR] [-u URL] [-p [PROXY ...]] [-t THREADS] [-s SLEEP] [-X METHOD] [-d DATA] [-H [HEADER ...]] [-b COOKIE] [--dry-run] [--ip IP] [-i {product,zip,chain}] [-e [EXT ...]] [--hc [HC ...]] [--hl [HL ...]] [--hw [HW ...]]
             [--hs [HS ...]] [--hr HR] [--sc [SC ...]] [--sl [SL ...]] [--sw [SW ...]] [--ss [SS ...]] [--sr SR] [--filter FILTER] [--hard-filter] [--auto-filter] [-L] [-R RECURSION] [-r PLUGIN_RECURSION] [-E] [--limit-requests LIMIT_REQUESTS] [--request-timeout REQUEST_TIMEOUT] [--domain-scope] [--plugin-threads PLUGIN_THREADS] [-V]

A Web Fuzzer. The options follow the curl schema where possible.

options:
  -h, --help            show this help message and exit
  -V, --version         Print version and exit.

Request building options:
  -u URL, --url URL     Specify a URL for the request.
  -p [PROXY ...], --proxy [PROXY ...]
                        Proxy requests. Use format 'protocol://ip:port'. Protocols SOCKS4, SOCKS5 and HTTP are supported. If supplied multipletimes, the requests will be split between all supplied proxies.
  -t THREADS, --threads THREADS
                        Modify the number of concurrent "threads"/connections for requests. (default: 40)
  -s SLEEP, --sleep SLEEP
                        Wait supplied seconds between requests.
  -X METHOD, --method METHOD
                        Set the HTTP method used for requests. (default: GET)
  -d DATA, --data DATA  Use POST method with supplied data (e.g. "id=FUZZ&catalogue=1"). Method can be overridden with --method.
  -H [HEADER ...], --header [HEADER ...]
                        Add/modify a header, e.g. "User-Agent: Changed". Multiple flags accepted.
  -b COOKIE, --cookie COOKIE
                        Add cookies, e.g. "Cookie1=foo; Cookie2=bar".
  --dry-run             Test run without actually making any HTTP request.
  --ip IP               Specify an IP to connect to. Format ip:port. Uses port 80 if none specified. This can help if you want to force connecting to a specific IP and still present a host name in the SNI, which will remain the URL's host.
  -i {product,zip,chain}, --iterator {product,zip,chain}
                        Set the iterator used when combining multiple wordlists. (default: product)
  -e [EXT ...], --ext [EXT ...]
                        Specify extensions to be appended to the wordlist items e.g. ".aspx,.asmx"

Response processing options:
  -L, --location        Follow redirections by sending an additional request to the redirection URL if it's in scope.
  -R RECURSION, --recursion RECURSION
                        Enable recursive path discovery by specifying a maximum depth.
  -r PLUGIN_RECURSION, --plugin-recursion PLUGIN_RECURSION
                        Adjust the max depth for recursions originating from plugins. Matches --recursion by default.
  -E, --stop-error      Stop on any connection error.
  --limit-requests LIMIT_REQUESTS
                        Limit recursions. Once specified amount of requests are sent, recursions will be deactivated
  --request-timeout REQUEST_TIMEOUT
                        Change the maximum seconds the request is allowed to take. (default: 40)
  --domain-scope        Base the scope check on the domain name instead of IP.
  --plugin-threads PLUGIN_THREADS
                        Modify the amount of threads used for concurrent execution of plugins. (default: 3)

Input/Output options:
  -w [WORDLIST ...], --wordlist [WORDLIST ...]
                        Specify a wordlist file to iterate through.
  -o OUTPUT, --output OUTPUT
                        Store results in the specified output file.
  -f {json,html,all}, --output-format {json,html,all}
                        Set the format of the output file. If you specify "all", each format will be used as a suffix for the specified output path. (default: json)
  -l DEBUG_LOG, --debug-log DEBUG_LOG
                        Store runtime information in the specified file.
  --dump-config DUMP_CONFIG
                        Write all supplied options to a config file and exit.
  -K CONFIG, --config CONFIG
                        Read config from specified path.
  --plugins [PLUGINS ...]
                        Plugins to be run, supplied as a list of plugin-files or plugin-categories
  --cache-dir CACHE_DIR
                        Specify a directory to read cached requests from.

Terminal options:
  -c, --colorless       Disable colors in CLI output.
  -q, --quiet           Disable progress messages in CLI output.
  -n, --noninteractive  Disable runtime interactions.
  -v, --verbose         Enable verbose information in CLI output.

Filter options:
  --hc [HC ...]         Hide responses matching the supplied codes (e.g. --hc 302 404 405).
  --hl [HL ...]         Hide responses matching the supplied lines.
  --hw [HW ...]         Hide responses matching the supplied words.
  --hs [HS ...]         Hide responses matching the supplied sizes/chars.
  --hr HR               Hide responses matching the supplied regex.
  --sc [SC ...]         Show responses matching the supplied codes.
  --sl [SL ...]         Show responses matching the supplied lines.
  --sw [SW ...]         Show responses matching the supplied words.
  --ss [SS ...]         Show responses matching the supplied sizes/chars.
  --sr SR               Show responses matching the supplied regex.
  --filter FILTER       Show/hide responses using the supplied regex.
  --hard-filter         Don't only hide the responses, but also prevent post processing of them (e.g. sending to plugins).
  --auto-filter         Filter automatically during runtime. If a response occurs too often, it will get filtered out.
```

### Example
```
wenum --hard-filter --plugins=default,gau,domainpath,clone,context,linkparser,sourcemap,robots,listing,sitemap,headers,backups,errors,title,links --hc 404 --auto-filter -R 2 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0' -w ~/wordlists/onelistforallmicro.txt  -e .aspx,.html -e .txt -f json -o example.com -u http://example.com/FUZZ
```

For a detailed documentation, please refer to the [wiki](https://github.com/WebFuzzForge/wenum/wiki).
