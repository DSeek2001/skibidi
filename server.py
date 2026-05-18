#!/usr/bin/env python3
import argparse
import base64
import os
import socket
import sys

BUFFER_SIZE = 65536


def normalize_path(root, path):
    path = os.path.normpath(path).lstrip("/\\")
    resolved = os.path.abspath(os.path.join(root, path))
    if not resolved.startswith(root):
        raise ValueError("Access outside root is not allowed")
    return resolved


def list_directory(root, rel_path):
    target = normalize_path(root, rel_path)
    if not os.path.exists(target):
        return "ERROR Path does not exist\n"
    if not os.path.isdir(target):
        return "ERROR Path is not a directory\n"
    entries = os.listdir(target)
    entries.sort()
    lines = []
    for name in entries:
        full = os.path.join(target, name)
        entry_type = "DIR" if os.path.isdir(full) else "FILE"
        lines.append(f"{entry_type} {name}")
    return "OK " + str(len(lines)) + "\n" + "\n".join(lines) + "\n"


def handle_download(root, rel_path, conn_file):
    target = normalize_path(root, rel_path)
    if not os.path.exists(target) or not os.path.isfile(target):
        conn_file.write(b"ERROR File does not exist\n")
        conn_file.flush()
        return
    size = os.path.getsize(target)
    conn_file.write(f"OK {size}\n".encode())
    conn_file.flush()
    with open(target, "rb") as f:
        while True:
            data = f.read(BUFFER_SIZE)
            if not data:
                break
            conn_file.write(data)
    conn_file.flush()


def handle_upload(root, rel_path, size, conn_file):
    target = normalize_path(root, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    remaining = int(size)
    with open(target, "wb") as f:
        while remaining > 0:
            chunk = conn_file.read(min(BUFFER_SIZE, remaining))
            if not chunk:
                raise IOError("Connection closed during upload")
            f.write(chunk)
            remaining -= len(chunk)
    conn_file.write(b"OK\n")
    conn_file.flush()


def handle_client(conn, addr, root, secret):
    conn_file = conn.makefile("rwb")
    try:
        auth_line = conn_file.readline().decode("utf-8", errors="replace").strip()
        if not auth_line.startswith("AUTH "):
            conn_file.write(b"ERROR Authentication required\n")
            conn_file.flush()
            return
        token = auth_line[5:]
        if token != secret:
            conn_file.write(b"ERROR Invalid secret\n")
            conn_file.flush()
            return
        conn_file.write(b"OK Welcome\n")
        conn_file.flush()

        while True:
            line = conn_file.readline().decode("utf-8", errors="replace")
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            parts = line.split(" ", 2)
            command = parts[0].upper()
            if command == "QUIT":
                conn_file.write(b"OK Goodbye\n")
                conn_file.flush()
                break
            elif command == "LIST":
                path = parts[1] if len(parts) > 1 else "."
                conn_file.write(list_directory(root, path).encode())
                conn_file.flush()
            elif command == "DOWNLOAD":
                if len(parts) < 2:
                    conn_file.write(b"ERROR Missing path\n")
                    conn_file.flush()
                    continue
                handle_download(root, parts[1], conn_file)
            elif command == "UPLOAD":
                if len(parts) < 3:
                    conn_file.write(b"ERROR Missing path or size\n")
                    conn_file.flush()
                    continue
                path = parts[1]
                size = parts[2]
                handle_upload(root, path, size, conn_file)
            else:
                conn_file.write(b"ERROR Unknown command\n")
                conn_file.flush()
    finally:
        conn_file.close()
        conn.close()


def run_server(host, port, root, secret):
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        raise ValueError(f"Root path does not exist: {root}")
    print(f"Server root={root} listening on {host}:{port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)
        while True:
            conn, addr = sock.accept()
            print(f"Connection from {addr}")
            try:
                handle_client(conn, addr, root, secret)
            except Exception as exc:
                print(f"Client error: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple remote file server. Run on the machine at home.")
    parser.add_argument("--host", default="0.0.0.0", help="Listen address")
    parser.add_argument("--port", type=int, default=9000, help="Listen port")
    parser.add_argument("--root", default=".", help="Root directory to expose")
    parser.add_argument("--secret", required=True, help="Shared secret for client authentication")
    args = parser.parse_args()
    run_server(args.host, args.port, args.root, args.secret)
