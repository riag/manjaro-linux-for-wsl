#!/bin/bash
# config.sh: to override built in defaults

EXTRA_PACKAGES+=(git)
EXTRA_PACKAGES+=(util-linux) # temp, should be added to manjaro-tools
EXTRA_PACKAGES+=(haveged) # for pacman-init
EXTRA_PACKAGES+=(manjaro-tools-pkg sudo gzip)
