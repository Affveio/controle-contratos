import pandas as pd
import json

file_path = r'c:\Users\Obra 369\Desktop\Planilha contrato\Contratos.xlsx'
output_path = r'c:\Users\Obra 369\Desktop\Planilha contrato\data.js'

df = pd.read_excel(file_path)
# Limpar dados (converter NaNs para None/null para o JSON)
df = df.where(pd.notnull(df), None)

data_json = df.to_json(orient='records')

with open(output_path, 'w', encoding='utf-8') as f:
    f.write('window.CONTRACT_DATA = ' + data_json)

print(f"Data saved to {output_path}")
