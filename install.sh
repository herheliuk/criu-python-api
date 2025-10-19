#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Please use 'source $(basename "$0")'"
    exit 1
fi

orig_pwd="$(pwd)"
script_dir="$(dirname "${BASH_SOURCE[0]}")"

source "$script_dir/env.sh"

cd "$script_dir"

sudo apt install build-essential git pkg-config \
    libprotobuf-dev libprotobuf-c-dev protobuf-c-compiler \
    protobuf-compiler python3-protobuf uuid-dev \
    libbsd-dev libcap-dev libnl-3-dev libnet1-dev \
    libaio-dev libgnutls28-dev libdrm-dev iproute2 \
    libnftables-dev asciidoc xmlto

git clone https://github.com/checkpoint-restore/criu ./criu/

sudo make -C ./criu/ install

pip install ./criu/lib/ ./
rm -rf ./*.egg-info ./build/

cd "$orig_pwd"
