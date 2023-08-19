# wenum

Maintained for Debian 10 and Kali, Python3.9+

## Installation

Poetry is the most recently tested way to install wenum. A typical workflow for installing could be:

First, it is recommended to create a [virtualenv](https://docs.python.org/3/library/venv.html) to avoid installing the project dependencies into the system packages:
```
# If unsure, go for sth like '/opt/wenum_venv'
mkdir $PATH_TO_VENV_FOLDER_OF_CHOICE
python3 -m venv $PATH_TO_VENV_FOLDER_OF_CHOICE
# Once created, only the source command is necessary to activate the venv in the future
# This works with bash. If 'fish' is used, use bin/activate.fish instead
source $PATH_TO_VENV_FOLDER_OF_CHOICE/bin/activate
```

Poetry probably won't be installed in the venv yet, therefore run:
`pip install poetry`

Debian-based distros may need the apt-packages `libssl-dev` and `libcurl4-openssl-dev`

Afterwards, the submodule commands will initialize linkfinder as the submodule, and lastly the project with its dependencies installed by poetry:
```
git clone $LINK_TO_REPO
cd wenum/
git submodule update --init --remote
poetry install
```


## Pulling changes ("Updating")
Since this repo contains linkfinder as a submodule, it is recommended to adjust the pulling command to include changes of it as well. Execute
`git pull --recurse-submodules` to pull those changes, too.

To ensure being in the newest commit of submodules (here: linkfinder), execute `git submodule update --remote`

## Usage

`wenum --help`

An example command utilizing a lot of the added functionality:
```
host="127.0.0.1:8081"
wenum --interact --hard-filter --script=default,gau,links,sourcemap,robots,sitemap,linkparser,domainpath -p 127.0.0.1:9999:SOCKS5 -R 2 -H 'User-Agent: SOMETHING' -w /usr/share/seclists/Discovery/Web-Content/common.txt --auto-filter --runtime-log -f wenum_out.json --hc 404 -F "https://$host/FUZZ"`
```

## Plugins

All the plugin files reside at `src/wenum/plugins/scripts`. Feel free to take a look at what kinds exist, adjust existing logic or write your own plugins. Should their use be generic, we can add them to the repo.

To utilize `gau`, you will need to install it first (it needs to be in your path): <https://github.com/lc/gau>