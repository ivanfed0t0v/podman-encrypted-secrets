#!/bin/env python3

import json
import os
import subprocess
import sys
from filelock import FileLock


def run_cmd(cmd, input):
    try:
        return subprocess.run(
            cmd,
            input=input,
            capture_output=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        print(e.stdout, file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        raise e


def encrypt_secret(secret_id, secret_value):
    cmd = ["systemd-creds", "encrypt", f"--name={secret_id}", "-", "-"]
    return run_cmd(cmd, secret_value).decode("utf-8")


def decrypt_secret(secret_id, encrypted_value):
    cmd = ["systemd-creds", "decrypt", f"--name={secret_id}", "-", "-"]
    return run_cmd(cmd, encrypted_value)


def store_secret(secrets_file, lock):
    secret_id = os.getenv("SECRET_ID")
    if not secret_id:
        print("SECRET_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    secret_value = sys.stdin.buffer.read()
    encrypted_value = encrypt_secret(secret_id, secret_value)
    with lock:
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
        secrets[secret_id] = encrypted_value.replace("\n", "")
        with open(secrets_file, "w") as f:
            json.dump(secrets, f)

    print(f"Secret '{secret_id}' created successfully")


def lookup_secret(secrets_file, lock):
    secret_id = os.getenv("SECRET_ID")
    if not secret_id:
        print("SECRET_ID environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    with lock, open(secrets_file, "r") as f:
        secrets = json.load(f)

    encrypted_value = secrets[secret_id]
    secret_value = decrypt_secret(secret_id, encrypted_value.encode("utf-8"))
    sys.stdout.buffer.write(secret_value)


def delete_secret(secrets_file, lock):
    secret_id = os.getenv("SECRET_ID")
    if not secret_id:
        print("SECRET_ID environment variable is not set", file=sys.stderr)
        sys.exit(1)

    with lock:
        with open(secrets_file, "r") as f:
            secrets = json.load(f)
        if secret_id in secrets:
            del secrets[secret_id]
            with open(secrets_file, "w") as f:
                json.dump(secrets, f)
            print(f"Secret '{secret_id}' deleted successfully")
        else:
            print(f"Secret '{secret_id}' not found", file=sys.stderr)


def list_secrets(secrets_file, lock):
    with lock, open(secrets_file, "r") as f:
        secrets = json.load(f)

    for secret_id in secrets:
        encrypted_value = secrets[secret_id]
        secret_value = decrypt_secret(secret_id, encrypted_value)
        print(secret_value)


def main():
    if len(sys.argv) < 2:
        print("Usage: podman-secrets.py <command> [secrets_path]")
        sys.exit(1)

    command = sys.argv[1]

    secrets_dir = sys.argv[2] if len(sys.argv) > 2 else "/var/lib/containers/storage/secrets/encrypted"
    if not os.path.exists(secrets_dir):
        os.makedirs(secrets_dir, exist_ok=True)
        os.chmod(secrets_dir, 0o700)

    secrets_file = os.path.join(secrets_dir, "secretsdata.json")
    lock = FileLock(os.path.join(secrets_dir, "secretsdata.lock"))

    with lock:
        if not os.path.exists(secrets_file):
            with open(secrets_file, "w") as f:
                json.dump({}, f)
            os.chmod(secrets_file, 0o600)

    try:
        if command == "store":
            store_secret(secrets_file, lock)
        elif command == "lookup":
            lookup_secret(secrets_file, lock)
        elif command == "delete":
            delete_secret(secrets_file, lock)
        elif command == "list":
            list_secrets(secrets_file, lock)
        else:
            print(f"Unknown command {command}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"{sys.argv[0]} error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
