
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    content = f.read()

start = content.find('return {')
if start == -1:
    print("Could not find 'return {'")
    sys.exit(1)

stack = 0
found_start = False
for i in range(start, len(content)):
    if content[i] == '{':
        stack += 1
        found_start = True
    elif content[i] == '}':
        stack -= 1
    
    if found_start and stack == 0:
        print(f"End of object at char {i}")
        print("Context around end:")
        print(content[i-50:i+50])
        # Find line number
        line_num = content.count('\n', 0, i) + 1
        print(f"Line number: {line_num}")
        break
else:
    print("Stack never reached 0. Unclosed braces!")
    print(f"Final stack: {stack}")
