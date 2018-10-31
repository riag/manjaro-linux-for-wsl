#!/bin/sh

export QT_SCALE_FACTOR=2
export GDK_SCALE=2

#export DISPLAY=:0
export DISPLAY=tcp/127.0.0.1:0

export LIBGL_ALWAYS_INDIRECT=1
export NO_AT_BRIDGE=1
