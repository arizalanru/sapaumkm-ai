import os


# Keep the suite isolated from local secrets and the development database.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GROQ_API_KEY"] = ""
