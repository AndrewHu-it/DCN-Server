# config.py
import os

class Config:
    """
    Holds all the configuration for our Flask app, including the MongoDB URI.
    In a real-world scenario, you might store your URI in an environment variable.
    """
    PORT = int(os.environ.get("PORT", 8000))  # The port on which to run Flask
    MONGODB_URI = os.environ.get(
        "MONGODB_URI",
        "mongodb+srv://ahurlbut999:MluzrXgAfj1Jf4yF@server-tasks.kszyt.mongodb.net/?retryWrites=true&w=majority&appName=Server-Tasks"
    )

