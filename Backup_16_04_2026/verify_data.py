import json
import os

filepath = r'c:\Users\Obra 369\Desktop\Planilha contrato\data.js'
if os.path.exists(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract ASSETS_DATA
    marker = 'window.ASSETS_DATA = '
    start = content.find(marker)
    if start != -1:
        start += len(marker)
        end = content.find('];', start) + 1
        assets_json = content[start:end]
        try:
            assets = json.loads(assets_json)
            if assets:
                print(f"Total assets: {len(assets)}")
                print(f"Sample asset keys: {list(assets[0].keys())}")
                # Check for Mes_Referencia
                months = set(a.get('Mes_Referencia') for a in assets if a.get('Mes_Referencia'))
                print(f"Available months in assets: {sorted(list(months))}")
                # Check for Status
                status_count = len([a for a in assets if a.get('Status')])
                print(f"Assets with Status field: {status_count}")
            else:
                print("ASSETS_DATA is empty")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
    else:
        print("ASSETS_DATA marker not found")
else:
    print("data.js not found")
