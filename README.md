# wenum

A wfuzz fork

We have taken the tool wfuzz as a base and gave it a little twist in its direction. 
We want to ease the process of mapping a web application's directory structure, and not spend too much attention on anything else (e.g. determining vulnerable states). 
The focus is therefore different, and unfortunately, some features will even be removed. 
That may be due to a feature clashing with the intended direction of wenum (e.g. the AllVarQueue), or simply because there are convenience features that we think are not important enough to maintain (e.g. manipulating the wordlist entries on the tool startup).

Maintained for Debian 10 and Kali, Python3.9+

## Usage

`wenum --help`

### Example
```
host="127.0.0.1:8081"
wenum --interact --hard-filter --script=default,gau,links,sourcemap,robots,sitemap,linkparser,domainpath -p 127.0.0.1:9999:SOCKS5 -R 2 -H 'User-Agent: SOMETHING' -w /usr/share/seclists/Discovery/Web-Content/common.txt --auto-filter --runtime-log -f wenum_out.json --hc 404 -F "https://$host/FUZZ"`
```

For a detailed documentation, please refer to the [wiki](https://github.com/WebFuzzForge/wenum/wiki)