import json
import re

with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Try to find month columns
months = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']

match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    if len(data) > 0:
        first = data[0]
        # print keys that look like months
        found_cols = []
        for k in first.keys():
            k_clean = str(k).upper()
            has_month = any(m in k_clean for m in months)
            if has_month and '/' in k_clean:
                found_cols.append(k)
        print("Data columns:")
        print(found_cols)
