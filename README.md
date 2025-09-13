> This project is an independent effort and is not affiliated with, sponsored by, or endorsed by CRIU (Checkpoint/Restore In Userspace).
> CRIU is licensed under GPLv2.

> Ubuntu x86_64 is recommended, linux system is requried.

## Install

```bash
# source env.sh
pip install git+https://github.com/herheliuk/criu-python-api
```

## Usage

main terminal
```bash
# source env.sh
python examples/example_usage.py
```

secondary terminal
```bash
tmux new-session 'python3 examples/process_to_dump.py'
```

## API Reference

Overrides the CRIU dumps directory. (optional)
```python
criu_api.set_dumps_dir("/tmp/criu_api_dumps")
```

Removes the dumps directory and all its contents.
```python
criu_api.clean_up()
```

Sets the target process ID.
```python
criu_api.set_pid(1240)
```

Creates a full dump, or an incremental dump if memory tracking is available.
```python
criu_api.dump(i, leave_running=True, allow_overwrite=False)
```

Restores the specified dump into the current terminal session.
```python
criu_api.restore(24, kill_if_exists=False)
```

## Install CRIU

```bash
sudo apt install build-essential git pkg-config \
    libprotobuf-dev libprotobuf-c-dev protobuf-c-compiler \
    protobuf-compiler python3-protobuf uuid-dev \
    libbsd-dev libcap-dev libnl-3-dev libnet1-dev \
    libaio-dev libgnutls28-dev libdrm-dev iproute2 \
    libnftables-dev asciidoc xmlto

git clone https://github.com/checkpoint-restore/criu.git
cd criu

sudo make install

cd ..
rm -rf criu/
```
