from pwdlib import PasswordHash
from datetime import datetime
import secrets

# 使用推荐方法创建PasswordHash对象
password_hasher = PasswordHash.recommended()

def generate_account() -> str:
    time = datetime.now().strftime("%Y%m%d%H")
    numbers = secrets.randbelow(10000)
    return time + f"{numbers:04d}"

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)