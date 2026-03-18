#!/usr/local/env bash

rsync -rv --progress --exclude-from .sync-exclude/run/media/justin/CIRCUITPY/ ./
