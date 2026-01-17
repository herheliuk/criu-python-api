#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "Please use 'source $(basename "$0")'"
    exit 1
fi

orig_pwd="$(pwd)"
script_dir="$(dirname "${BASH_SOURCE[0]}")"

source "$script_dir/env.sh"

cd "$script_dir"

git clone https://github.com/checkpoint-restore/criu --depth 1

sudo bash ./criu/contrib/dependencies/apt-packages.sh
sudo make -C ./criu/ install -j$(nproc) || return 1

pip install ./criu/lib/
rm -rf ./*.egg-info ./build/

cd "$orig_pwd"
