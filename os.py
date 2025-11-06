import dash
import hashlib
import pandas as pd

def hash_code(name):
    return hashlib.sha256(name.encode()).hexdigest()

data = pd.read_csv("athlete_events.csv")
mask = (data["Team"] == "France")
data = data[mask]
data["Name"] = data["Name"].apply(hash_code)
print(data["Team"])