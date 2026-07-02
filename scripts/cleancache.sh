#! /bin/bash

set -xe

find . -name "__pycache__" -exec sudo rm -rf {} +
