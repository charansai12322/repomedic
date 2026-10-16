import hashlib
import subprocess

def hash_data(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def list_files(path: str) -> None:
    subprocess.run(['ls', '-la', path], shell=False, check=True)
