#!/bin/sh

DIR=/usr/local/bin

set -x
sudo cp led $DIR
sudo cp led-batt $DIR
sudo cp bash_completion.d/* /etc/bash_completion.d
