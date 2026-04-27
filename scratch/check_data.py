import json
import os

if os.path.exists('data.js'):
    with open('data.js', encoding='utf-8') as f:
        content = f.read()
    
    marker = 'window.ASSETS_DATA = '
    start = content.find(marker)
    if start != -1:
        start += len(marker)
        end = content.find(';', start)
        if end != -1:
            json_str = content[start:end]
            data = json.loads(json_str)
            print(f"Total Assets: {len(data)}")
            cad_count = len([x for x in data if str(x.get('asset_id', '')).startswith('CAD_')])
            mnt_count = len([x for x in data if str(x.get('asset_id', '')).startswith('MNT_')])
            print(f"CAD Assets: {cad_count}")
            print(f"MNT Assets: {mnt_count}")
            
            # Check unique Obra values
            obras = set(str(x.get('Obra', '')) for x in data)
            print(f"Unique Obras in data: {obras}")
            
            # Check CAD items specifically
            cad_items = [x for x in data if str(x.get('asset_id', '')).startswith('CAD_')]
            if cad_items:
                print(f"Total CAD items: {len(cad_items)}")
                cad_obras = set(str(x.get('Obra', '')) for x in cad_items)
                print(f"Unique CAD Obras: {cad_obras}")
                cad_months = set(str(x.get('Mes_Referencia', '')) for x in cad_items)
                print(f"Unique CAD Months: {cad_months}")
                print(f"Sample CAD Item: {cad_items[0]}")
            
            # Check ONIBUS specifically
            bus_items = [x for x in data if 'ONIBUS' in str(x.get('Equipamento', '')).upper()]
            if bus_items:
                print(f"Total Bus items: {len(bus_items)}")
                print(f"Sample Bus: {bus_items[0]}")
                print(f"Bus ValorHora list (first 10): {[x.get('ValorHora') for x in bus_items[:10]]}")
    else:
        print("Marker not found")
else:
    print("File not found")
