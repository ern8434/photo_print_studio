pyinstaller --noconfirm --onefile --windowed --icon=logo.png  \
--add-data ".venv/lib/python3.12/site-packages/customtkinter:customtkinter/" \
main.py
