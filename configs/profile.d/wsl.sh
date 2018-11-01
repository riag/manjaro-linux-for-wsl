#!/bin/sh

IS_WSL=`grep -i microsoft /proc/version`

export IS_WSL
