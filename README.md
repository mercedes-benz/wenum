# wenum

A wfuzz fork

We have taken the tool wfuzz as a base and gave it a little twist in its direction. 
We want to ease the process of mapping a web application's directory structure, and not spend too much attention on anything else (e.g. determining vulnerable states). 
The focus is therefore different, and unfortunately, some features will even be removed. 
That may be due to a feature clashing with the intended direction of wenum (e.g. the AllVarQueue), or simply because there are convenience features that we think are not important enough to maintain (e.g. manipulating the wordlist entries on the tool startup).

Maintained for Debian 10 and Kali, Python3.10+

## Usage

`wenum --help`

### Example
```
wenum --hard-filter --plugins=default,gau,domainpath,clone,context,linkparser,sourcemap,robots,listing,sitemap,headers,backups,errors,title,links --hc 404 --auto-filter -R 2 -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0' -w ~/wordlists/onelistforallmicro.txt -f json -o example.com -u http//example.com/FUZZ
```

For a detailed documentation, please refer to the [wiki](https://github.com/WebFuzzForge/wenum/wiki).
