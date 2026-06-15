# -*- coding: utf-8 -*-
import os, sys, io
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-logging'
os.environ['QT_LOGGING_RULES'] = '*.debug=false;*.info=false;*.warning=false'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0]]

old_out, old_err = sys.stdout, sys.stderr
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()
try:
    exec(open('test_editor.py', encoding='utf-8').read())
except SystemExit:
    pass
finally:
    out = sys.stdout.getvalue()
    sys.stdout, sys.stderr = old_out, old_err

for line in out.split('\n'):
    if any(kw in line for kw in ['PASS','FAIL','SKIP','测试','---','===','结果','通过','ERROR']):
        print(line)