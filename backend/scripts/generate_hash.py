import getpass
import bcrypt


def main():
    print("=== Admin Password Hash Generator ===")
    print("This script generates a secure bcrypt hash for your admin password.")
    print(
        "You will save this hash in your .env file instead of "
        "the plain-text password.\\n"
    )

    password = getpass.getpass("Enter your desired admin password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt)

    escaped_hash = hashed_password.decode("utf-8").replace("$", "$$")

    print("\\nSuccess! Here is your bcrypt hash:")
    print("-" * 50)
    print(escaped_hash)
    print("-" * 50)
    print(
        "\\nCopy the above hash and place it in your backend/.env file like this:\\n"
        "(Note: The '$' symbols are escaped as '$$' to work with Docker Compose)"
    )
    print(f"ADMIN_PASSWORD_HASH={escaped_hash}")


if __name__ == "__main__":
    main()
