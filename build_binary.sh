pyinstaller --noconfirm --onefile --windowed \
--hidden-import "PIL._tkinter_finder" \
--add-data ".venv/lib/python3.12/site-packages/customtkinter:customtkinter/" \
--add-data "logo.png:." \
main.py
