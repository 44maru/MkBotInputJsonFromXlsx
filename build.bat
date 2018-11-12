@echo off

call venv\Scripts\activate
rem pyInstaller --onefile --noconsole jsonMaker.py
pyInstaller jsonmaker.spec
move dist\jsonMaker.exe dist\‘å˜aŒ^slayer•â•ƒc[ƒ‹.exe

pause