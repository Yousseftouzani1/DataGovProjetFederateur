from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

SECRET_KEY = "SUPER_SECRET_KEY_ABC123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# FIX: use sha256_crypt instead of bcrypt
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def hash_password(password):
    print("DEBUG → password received:", password, type(password))
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
