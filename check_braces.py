
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    content = f.read()

start_tag = '<script>'
end_tag = '</script>'
start_idx = content.rfind(start_tag)
end_idx = content.find(end_tag, start_idx)

script = content[start_idx + len(start_tag):end_idx]

stack = []
for i, char in enumerate(script):
    if char == '{':
        stack.append(i)
    elif char == '}':
        if not stack:
            print("EXTRA CLOSE BRACE at " + str(i))
            print(script[max(0, i-20):i+20])
        else:
            stack.pop()

print("Final stack size: " + str(len(stack)))
if stack:
    for s in stack:
        print("Unclosed brace at " + str(s))
        print(script[s:s+40])
