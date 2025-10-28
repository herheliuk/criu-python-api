> This project is an independent effort and is not affiliated with, sponsored by, or endorsed by CRIU (Checkpoint/Restore In Userspace).
> CRIU is licensed under GPLv2.

> Ubuntu x86_64 is recommended, linux system is requried.

## Install (Ubuntu/Debian)

```bash
# source env.sh
# mkdir ./criu-python-api/
git clone https://github.com/herheliuk/criu-python-api ./criu-python-api/ --depth 1
source ./criu-python-api/install.sh
```

## Usage

main terminal
```bash
# source env.sh
sudo -E $(which python) ./examples/cli_knockdown.py
```

secondary terminal
```bash
tmux new-session 'python3 ./examples/process_to_dump.py'
```

## API Reference

Overrides the dumps directory. (optional, `./criu_dumps/` by default)
```python
criu_api.set_dumps_dir("/tmp/criu_api_dumps/")
```

Removes dumps directory and all its contents!
```python
criu_api.wipe()
```

Sets the target process ID.
```python
criu_api.set_pid(1544)
```

Creates full or incremental dump if memory tracking is available.
```python
criu_api.dump(
    i, # dump_number (optional)
    # leave_running = True
    # ensure_full_dump = False
    # allow_overwrite = False
    # additional_args = None # list[str]
)
```

Restores specified dump into current terminal session.
```python
criu_api.restore(
    11, # dump_number (optional)
    # kill_if_exists = False,
    # additional_args = None # list[str]
)
```
