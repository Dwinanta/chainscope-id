import ast
src = open('app.py', encoding='utf-8').read()
ast.parse(src)
print('app.py: syntax OK, lines:', src.count(chr(10)))
