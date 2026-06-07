from pathlib import Path
import hashlib
import secrets

try:
    import bcrypt
except ImportError:
    bcrypt = None


def hash_password(password: str) -> str:
    if bcrypt:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    salt = secrets.token_hex(8)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return f"sha256${salt}${digest}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if hashed_password.startswith("sha256$"):
        _, salt, digest = hashed_password.split("$", 2)
        return hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest() == digest
    if bcrypt:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    return plain_password == hashed_password


def hash_filename(filename: str) -> str:
    filestem = Path(filename).stem
    file_extension = Path(filename).suffix
    digest = hashlib.sha256((filestem + secrets.token_hex(4)).encode("utf-8")).hexdigest()
    return f"{digest}{file_extension}"
