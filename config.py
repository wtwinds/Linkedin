import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")



# MONGO_URI = "mongodb+srv://wtwinds26_db_user:3X1Ck3momZJLg6pp@cluster0.wkjccr9.mongodb.net/wtwinds"

# SECRET_KEY = "wtwinds_secret"

# MAIL_SERVER = "smtp.gmail.com"
# MAIL_PORT = 587
# MAIL_USE_TLS = True

# MAIL_USERNAME = "lalitmahajan.wtwinds@gmail.com"   
# MAIL_PASSWORD = "usjtphtsrojltotd"    