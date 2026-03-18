#!/usr/local/env bash

rsync -rv --progress --whole-file --delay-updates --exclude-from .sync-exclude ./ /run/media/justin/CIRCUITPY
