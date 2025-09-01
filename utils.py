from datetime import datetime
import re

def now_date_str():
    return datetime.now().strftime("%d/%m/%Y")

def parse_amount(text: str):
    """Try to parse numeric amount from text. Returns float or raise ValueError"""
    # Allow things like "100", "100.50", "₹50", "50 INR"
    t = text.strip().replace("₹", "")
    t = re.sub(r"[^\d\.\-]", "", t)  # keep digits, dot, minus
    if t == "":
        raise ValueError("No amount found")
    return float(t)
