import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

MAX_PAGE_TEXT_CHARS = 4000
MAX_ELEMENTS = 200
MAX_STEPS = 25
MAX_INPUT_ELEMENTS = 30
SECURITY_CONFIRM_WORDS = ["pay", "order", "delete", "оплат", "заказ", "удал"]
