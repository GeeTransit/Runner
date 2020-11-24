python -m venv .venv
call .venv\scripts\activate
pip install pyinstaller
pyinstaller --onefile --distpath . runner.py
del runner.spec
rmdir /s /q build __pycache__ .venv
exit
:: Two options: deactivate then delete, or delete then deactivate.
:: Both don't work... If I deactivate, the shell exits. But if I delete, I
:: can't deactivate. Only way out is to force exit :/
