import bcrypt
def hash_password(password: str) -> str:
    password = password.encode("utf-8")
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    password = hashed.decode("utf-8")
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = plain_password.encode("utf-8")
    hashed_password = hashed_password.encode("utf-8")
    
    if bcrypt.checkpw(plain_password, hashed_password):
        print("It Matches!")
        return True
    else:
        print("It Does not Match :(")
        return False