#!/bin/bash

set -euo

mkdir -p .env
mkdir -p .conf

cp -r .env.example/* .env/
cp -r .conf.example/* .conf/