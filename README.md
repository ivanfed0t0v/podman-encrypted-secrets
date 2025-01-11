# Podman encrypted secrets

This script enables the encryption of Podman secrets using [systemd credentials](https://systemd.io/CREDENTIALS/). It is implemented as a [shell driver](https://docs.podman.io/en/stable/markdown/podman-secret-create.1.html#secret-drivers).

## Installation

1. Install `python-filelock` with your system package manager. Do NOT use pip, it might break your system.
2. Make sure you looked at the source and understand what this script does. Don't just blindly run random scripts from the Internet on your system.
3. Download this script and save it as `/usr/local/bin/podman-encrypted-secrets.py`

    ```sh
    sudo wget -O /usr/local/bin/podman-encrypted-secrets.py https://raw.githubusercontent.com/ivanfed0t0v/podman-encrypted-secrets/refs/heads/main/podman-encrypted-secrets.py
    sudo chmod +x /usr/local/bin/podman-encrypted-secrets.py
    ```

4. Verify that everything is working. The command below should create file in `/var/lib/containers/storage/secrets/encrypted/secresdata.json` with encrypted secret:

    ```sh
    systemd-ask-password -n | sudo podman secret create --driver=shell "--driver-opts=list=/usr/local/bin/podman-encrypted-secrets.py list" "--driver-opts=lookup=/usr/local/bin/podman-encrypted-secrets.py lookup" "--driver-opts=store=/usr/local/bin/podman-encrypted-secrets.py store" "--driver-opts=delete=/usr/local/bin/podman-encrypted-secrets.py delete" test-encryption -
    ```

5. (Optional) Edit `/etc/containers/containers.conf` if you want to use encryption by default and avoid having to write `--driver` and `--driver-opts` parameters each time:

    ```toml
    [secrets]
    driver = "shell"

    [secrets.opts]
    list = "/usr/local/bin/podman-encrypted-secrets.py list"
    lookup = "/usr/local/bin/podman-encrypted-secrets.py lookup"
    store = "/usr/local/bin/podman-encrypted-secrets.py store"
    delete = "/usr/local/bin/podman-encrypted-secrets.py delete"
    ```
