# File to contain static data of plugins that may be shared or simply clutters the plugin file itself

head_extensions = [".gif", ".jpg", ".zip", ".png", ".exe", ".pdf", ".apk", ".ipa"]
valid_codes = [200, 301, 302, 303, 307, 308]

# Dictionary containing dir names that map to a specific technology
dir_to_tech = {
    "js": "js",
    "jsx": "jsx",
    "javascript": "js",
    "scripts": "js",
    "script": "js",
    "jsp": "jsp",
    "backup": "backup",
    "bak": "backup",
    "service": "service",
    "services": "service",
    "webservice": "service",
    "webservices": "service",
    "pdf": "pdf",
    "api": "api",
    "debug": "debug",
    "wsdl": "wsdl",
    "log": "log",
    "logs": "log"
}
extension_to_tech = {
    ".js": "js",
    ".jsx": "jsx",
    ".asp": "net",
    ".aspx": "net",
    ".ashx": "net",
    ".ashx": "service",
    ".htm": "html",
    ".php": "php"
}

extension_list = {
    "js": [
        ".js"
    ],
    "jsx": [
        ".jsx"
    ],

    "jsp": [
        ".jsp"
    ],

    "backup": [
        ".bak",
        ".zip",
        ".7z",
        ".tar.gz"
    ],

    "service": [
        ".svc",
        ".asmx",
        ".ashx"
    ],

    "api": [
        ""
    ],

    "debug": [
        ".dll"
    ],

    "net": [
        ".asp",
        ".aspx"
    ],

    "html": [
        ".htm",
        ".html"
    ],

    "pdf": [
        ".pdf"
    ],

    "php": [
        ".php"
    ],

    "wsdl": [
        ".wsdl"
    ],
    
    "log": [
        ".log",
        ".txt",
        ".zip",
        ".tar.gz"
    ]
}

ERRORS_regex_list = [
    "A syntax error has occurred",
    "ADODB.Field error",
    "ASP.NET is configured to show verbose error messages",
    "ASP.NET_SessionId",
    "Active Server Pages error",
    "An illegal character has been found in the statement",
    'An unexpected token "END-OF-STATEMENT" was found',
    "Can't connect to local",
    "Custom Error Message",
    "DB2 Driver",
    "DB2 Error",
    "DB2 ODBC",
    "Disallowed Parent Path",
    "Error Diagnostic Information",
    "Error Message : Error loading required libraries.",
    "Error Report",
    "Error converting data type varchar to numeric",
    "Fatal error",
    "Incorrect syntax near",
    "Internal Server Error",
    "Invalid Path Character",
    "Invalid procedure call or argument",
    "Invision Power Board Database Error",
    "JDBC Driver",
    "JDBC Error",
    "JDBC MySQL",
    "JDBC Oracle",
    "JDBC SQL",
    "Microsoft OLE DB Provider for ODBC Drivers",
    "Microsoft VBScript compilation error",
    "Microsoft VBScript error",
    "MySQL Driver",
    "MySQL Error",
    "MySQL ODBC",
    "ODBC DB2",
    "ODBC Driver",
    "ODBC Error",
    "ODBC Microsoft Access",
    "ODBC Oracle",
    "ODBC SQL",
    "ODBC SQL Server",
    "OLE/DB provider returned message",
    "ORA-0",
    "ORA-1",
    "Oracle DB2",
    "Oracle Driver",
    "Oracle Error",
    "Oracle ODBC",
    "PHP Error",
    "PHP Parse error",
    "PHP Warning",
    "Permission denied: 'GetObject'",
    "PostgreSQL query failed: ERROR: parser: parse error",
    r"SQL Server Driver\]\[SQL Server",
    "SQL command not properly ended",
    "SQLException",
    "Supplied argument is not a valid PostgreSQL result",
    "Syntax error in query expression",
    "The error occurred in",
    "The script whose uid is",
    "Type mismatch",
    "Unable to jump to row",
    "Unclosed quotation mark before the character string",
    "Unterminated string constant",
    "Warning: Cannot modify header information - headers already sent",
    "Warning: Supplied argument is not a valid File-Handle resource in",
    r"Warning: mysql_query\(\)",
    r"Warning: mysql_fetch_array\(\)",
    r"Warning: pg_connect\(\): Unable to connect to PostgreSQL server: FATAL",
    "You have an error in your SQL syntax near",
    "data source=",
    "detected an internal error [IBM][CLI Driver][DB2/6000]",
    "invalid query",
    "is not allowed to access",
    "missing expression",
    "mySQL error with query",
    "mysql error",
    "on MySQL result index",
    "supplied argument is not a valid MySQL result resource",
]

HEADERS_server_headers = ["server", "x-powered-by" "via"]

HEADERS_common_response_headers_regex_list = [
    r"^Server$",
    r"^X-Powered-By$",
    r"^Via$",
    r"^Access-Control.*$",
    r"^Accept-.*$",
    r"^age$",
    r"^allow$",
    r"^Cache-control$",
    r"^Client-.*$",
    r"^Connection$",
    r"^Content-.*$",
    r"^Cross-Origin-Resource-Policy$",
    r"^Date$",
    r"^Etag$",
    r"^Expires$",
    r"^Keep-Alive$",
    r"^Last-Modified$",
    r"^Link$",
    r"^Location$",
    r"^P3P$",
    r"^Pragma$",
    r"^Proxy-.*$",
    r"^Refresh$",
    r"^Retry-After$",
    r"^Referrer-Policy$",
    r"^Set-Cookie$",
    r"^Server-Timing$",
    r"^Status$",
    r"^Strict-Transport-Security$",
    r"^Timing-Allow-Origin$",
    r"^Trailer$",
    r"^Transfer-Encoding$",
    r"^Upgrade$",
    r"^Vary$",
    r"^Warning^$",
    r"^WWW-Authenticate$",
    r"^X-Content-Type-Options$",
    r"^X-Download-Options$",
    r"^X-Frame-Options$",
    r"^X-Microsite$",
    r"^X-Request-Handler-Origin-Region$",
    r"^X-XSS-Protection$",
]

HEADERS_common_req_headers_regex_list = [
    r"A-IM$",
    r"Accept$",
    r"Accept-.*$",
    r"Access-Control-.*$",
    r"Authorization$",
    r"Cache-Control$",
    r"Connection$",
    r"Content-.*$",
    r"Cookie$",
    r"Date$",
    r"Expect$",
    r"Forwarded$",
    r"From$",
    r"Host$",
    r"If-.*$",
    r"Max-Forwards$",
    r"Origin$",
    r"Pragma$",
    r"Proxy-Authorization$",
    r"Range$",
    r"Referer$",
    r"TE$",
    r"User-Agent$",
    r"Upgrade$",
    r"Upgrade-Insecure-Requests$",
    r"Via$",
    r"Warning$",
    r"X-Requested-With$",
    r"X-HTTP-Method-Override$",
    r"X-Requested-With$",
]

LISTING_dir_indexing_regexes = ["<title>Index of /",
                                '<a href="\\?C=N;O=D">Name</a>',
                                "Last modified</a>",
                                "Parent Directory</a>",
                                "Directory Listing for",
                                "<TITLE>Folder Listing.",
                                "<TITLE>Folder Listing.",
                                '<table summary="Directory Listing" ',
                                "- Browsing directory ",
                                '">\\[To Parent Directory\\]</a><br><br>',
                                '<A HREF=".*?">.*?</A><br></pre><hr></body></html>']
