import getpass
import bcrypt

def main():
    print("=== Admin Password Hash Generator ===")
    print("This script generates a secure bcrypt hash for your admin password.")
    print("You will save this hash in your secrets.toml file instead of the plain-text password.\\n")
    
    password = getpass.getpass("Enter your desired admin password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        print("Error: Passwords do not match.")
        return

    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    print("\\nSuccess! Here is your bcrypt hash:")
    print("-" * 50)
    print(hashed_password.decode('utf-8'))
    print("-" * 50)
    print("\\nCopy the above hash and place it in your backend/secrets.toml file like this:")
    print(f'admin_password_hash = "{hashed_password.decode("utf-8")}"')

if __name__ == "__main__":
    main()
