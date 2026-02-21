import customtkinter as ctk

app = ctk.CTk()

btn_frame = ctk.CTkFrame(app, fg_color="blue")
btn_frame.pack(side="bottom", fill="x", padx=20, pady=20)
print(btn_frame.winfo_exists())

app.update()
