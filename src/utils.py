import pandas as pd
import unicodedata
import re

def normalize(name):
    if pd.isna(name):
        return ""
    name = str(name).lower().strip()
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return name

def safe(df, col, default=0):
    return df[col] if col in df.columns else default
