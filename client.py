#!/usr/bin/env python3
import argparse
import os
import socket
import sys

BUFFER_SIZE = 65536


def receive_line(sock_file):
    line = sock_file.readline().decode("utf-8", errors="replace")
    if not line:
        raise IOError("Connection closed by server")
    return line.strip()


def send_command(sock_file, command):
    sock_file.write((command + "\n").encode())
    sock_file.flush()


def run_client(host, port, secret):
    with socket.create_connection((host, port)) as sock:
        sock_file = sock.makefile("rwb")
        send_command(sock_file, f"AUTH {secret}")
        response = receive_line(sock_file)
        if not response.startswith("OK"):
            print("Authentication failed:", response)
            return
        print(response)

        while True:
            try:
                command_line = input("remote> ").strip()
            except EOFError:
                command_line = "QUIT"
            if not command_line:
                continue
            parts = command_line.split()
            cmd = parts[0].lower()
            if cmd == "exit" or cmd == "quit":
                send_command(sock_file, "QUIT")
                print(receive_line(sock_file))
                break
            elif cmd == "list":
                path = parts[1] if len(parts) > 1 else "."
                send_command(sock_file, f"LIST {path}")
                response = receive_line(sock_file)
                if not response.startswith("OK "):
                    print(response)
                    continue
                count = int(response.split()[1])
                for _ in range(count):
                    print(receive_line(sock_file))
            elif cmd == "download":
                if len(parts) != 3:
                    print("Usage: download <remote-path> <local-path>")
                    continue
                remote_path, local_path = parts[1], parts[2]
                send_command(sock_file, f"DOWNLOAD {remote_path}")
                response = receive_line(sock_file)
                if not response.startswith("OK "):
                    print(response)
                    continue
                size = int(response.split()[1])
                with open(local_path, "wb") as f:
                    remaining = size
                    while remaining > 0:
                        chunk = sock_file.read(min(BUFFER_SIZE, remaining))
                        if not chunk:
                            raise IOError("Connection closed during download")
                        f.write(chunk)
                        remaining -= len(chunk)
                print(f"Downloaded {remote_path} -> {local_path} ({size} bytes)")
            elif cmd == "upload":
                if len(parts) != 3:
                    print("Usage: upload <local-path> <remote-path>")
                    continue
                local_path, remote_path = parts[1], parts[2]
                if not os.path.isfile(local_path):
                    print("Local file does not exist:", local_path)
                    continue
                size = os.path.getsize(local_path)
                send_command(sock_file, f"UPLOAD {remote_path} {size}")
                with open(local_path, "rb") as f:
                    while True:
                        data = f.read(BUFFER_SIZE)
                        if not data:
                            break
                        sock_file.write(data)
                    sock_file.flush()
                response = receive_line(sock_file)
                print(response)
            else:
                print("Commands: list [path], download <remote> <local>, upload <local> <remote>, quit")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple remote file client. Run on your computer.")
    parser.add_argument("--host", required=True, help="Server host")
    parser.add_argument("--port", type=int, default=9000, help="Server port")
    parser.add_argument("--secret", required=True, help="Shared secret for server authentication")
    args = parser.parse_args()
    run_client(args.host, args.port, args.secret)
