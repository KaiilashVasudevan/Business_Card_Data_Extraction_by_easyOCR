import pickle
from pathlib import Path
import streamlit_authenticator as stauth

# Defining the Names and passwords
# Creating list of users
names = ["administrator","manager"]
# Defining usernames used for authentication
usernames = ["admin", "manager"]
# Defining passwords for the above users
passwords = ["vasudevan", "kaiilash"]

# Using Hasher module to convert the plain text passwords into Hashed passwords
# Note: Streamlit Authenticator uses bcrypt for password hashing - secured Algorithms
hashed_passwords = stauth.Hasher(passwords).generate()
# Store the password in pickle file and store in the working directory

file_path = Path(__file__).parent / "hashed_pw.pkl"
# Open the file in wide binary mode and dump our password
with file_path.open("wb") as file:
    pickle.dump(hashed_passwords, file)