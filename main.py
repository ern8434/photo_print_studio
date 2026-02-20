# main.py
import os
import platform
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from config import PAPER_SIZES, DEFAULT_MARGIN, PHOTO_WIDTH, PHOTO_HEIGHT
from layout_engine import calculate_grid, get_coordinates
from image_processor import load_and_crop_image, generate_layout_canvas, get_preview_image, save_high_quality

# Görünüm ayarları
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PhotoPrintApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Fotoğraf Baskı Yerleşim Otomasyonu")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # Durum değişkenleri
        self.selected_image_path = None
        self.cropped_image = None
        self.current_canvas = None # Gerçek 300DPI tuval resmi
        
        self.paper_keys = list(PAPER_SIZES.keys())
        self.selected_paper_key = self.paper_keys[0] # Varsayılan: ilk kağıt
        
        # Grid bilgisi önbelleği
        self.current_grid_info = None

        # -- Grid Konfigürasyonu --
        self.grid_columnconfigure(0, weight=1, minsize=350)  # Sol panel (daha küçük)
        self.grid_columnconfigure(1, weight=3) # Sağ panel (önizleme)
        self.grid_rowconfigure(0, weight=1)

        # 1. SOL PANEL (Kontroller)
        self.setup_left_panel()

        # 2. SAĞ PANEL (Önizleme)
        self.setup_right_panel()
        
        # İlk yükleme durumu
        self.update_paper_selection(self.selected_paper_key)

    def setup_left_panel(self):
        self.left_frame = ctk.CTkFrame(self, corner_radius=10)
        self.left_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # Başlık
        self.title_label = ctk.CTkLabel(self.left_frame, text="Baskı Ayarları", font=ctk.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=(20, 20))

        # --- Resim Seçimi ---
        self.img_btn = ctk.CTkButton(self.left_frame, text="Vesikalık Resim Seç", command=self.select_image)
        self.img_btn.pack(pady=10, padx=20, fill="x")

        self.img_status_label = ctk.CTkLabel(self.left_frame, text="Henüz resim seçilmedi", font=ctk.CTkFont(size=12, slant="italic"))
        self.img_status_label.pack(pady=(0, 20))

        # --- Kağıt Boyutu ---
        self.paper_label = ctk.CTkLabel(self.left_frame, text="Kağıt Boyutu (300 DPI):")
        self.paper_label.pack(anchor="w", padx=20)

        self.paper_combo = ctk.CTkComboBox(self.left_frame, values=self.paper_keys, command=self.update_paper_selection)
        self.paper_combo.set(self.selected_paper_key)
        self.paper_combo.pack(pady=(5, 20), padx=20, fill="x")

        # --- Kenar Boşluğu (Margin) ---
        self.margin_label = ctk.CTkLabel(self.left_frame, text=f"Kenar Boşluğu (px): {DEFAULT_MARGIN}")
        self.margin_label.pack(anchor="w", padx=20)

        self.margin_slider = ctk.CTkSlider(self.left_frame, from_=0, to=200, number_of_steps=200, command=self.update_margin_label)
        self.margin_slider.set(DEFAULT_MARGIN)
        self.margin_slider.pack(pady=(5, 20), padx=20, fill="x")

        # --- Adet Sürgüsü ---
        self.count_label = ctk.CTkLabel(self.left_frame, text="Adet (1):")
        self.count_label.pack(anchor="w", padx=20)

        # Başlangıçta 1-1, resim seçildiğinde ve kağıt hesaplandığında güncellenir
        self.count_slider = ctk.CTkSlider(self.left_frame, from_=1, to=2, number_of_steps=1, command=self.update_count_label)
        self.count_slider.set(1)
        self.count_slider.pack(pady=(5, 5), padx=20, fill="x")
        
        self.max_count_label = ctk.CTkLabel(self.left_frame, text="Max: 1 adet sığabilir", text_color="gray", font=ctk.CTkFont(size=11))
        self.max_count_label.pack(pady=(0, 20), anchor="w", padx=20)
        
        # Alt bölme için boşluk
        self.spacer = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.spacer.pack(fill="both", expand=True)

        # --- İşlem Butonları (Kaydet / Yazdır) ---
        self.action_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.action_frame.pack(side="bottom", fill="x", pady=20, padx=20)

        self.save_btn = ctk.CTkButton(self.action_frame, text="Yüksek Kalite\nKaydet (JPG)", command=self.save_final_image, fg_color="#2b7b46", hover_color="#1f5c34")
        self.save_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.print_btn = ctk.CTkButton(self.action_frame, text="Sistemden\nYazdır", command=self.print_image, fg_color="#1f538d", hover_color="#14375e")
        self.print_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

    def setup_right_panel(self):
        self.right_frame = ctk.CTkFrame(self, corner_radius=10)
        self.right_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.right_frame.grid_columnconfigure(0, weight=1)
        self.right_frame.grid_rowconfigure(0, weight=1)

        # Canvas (Önizleme gösterimi için bir Canvas/Label kullanıyoruz)
        self.preview_label = ctk.CTkLabel(self.right_frame, text="Canlı Önizleme Alanı\n\n(Lütfen sol panelden bir resim seçin)", font=ctk.CTkFont(size=16), text_color="gray")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    # --- Olay (Event) Fonksiyonları ---

    def select_image(self):
        file_path = filedialog.askopenfilename(
            title="Resim Seç",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        if file_path:
            self.selected_image_path = file_path
            filename = os.path.basename(file_path)
            self.img_status_label.configure(text=f"Seçilen: {filename[:20]}...", text_color="green")
            
            # Resmi akıllı kırp (3.5x4.5 cm / 300DPI = 413x531 px)
            self.cropped_image = load_and_crop_image(self.selected_image_path)
            
            # Yeni resim yüklendiğinde, geçerli kağıt ve adet limitlerine göre önizlemeyi yenile
            self.refresh_layout()

    def update_paper_selection(self, choice):
        self.selected_paper_key = choice
        self.refresh_layout()

    def update_margin_label(self, value):
        margin_val = int(value)
        self.margin_label.configure(text=f"Kenar Boşluğu (px): {margin_val}")
        
        # Sürükleme bittiğinde sürekli çizmek maliyetli olabilir, bu yüzden fareyi bıraktığında render etmek mantıklı
        # ama ctk slider sürekli komut atar, optimize bir çözüm için doğrudan bağlıyoruz:
        self.refresh_layout()
        
    def update_count_label(self, value):
        count_val = int(value)
        
        # Max limiti aşmasını slider kendisi koruyor (to=max_val sayesinde)
        # Sadece görseli yeniliyoruz.
        self.count_label.configure(text=f"Adet ({count_val}):")
        self.refresh_layout(update_sliders=False)

    def refresh_layout(self, update_sliders=True):
        """
        Giriş verilerine göre grid hesaplamalarını günceller
        Önizleme tuvalini çizer. update_sliders True ise max slider limitlerini
        matematiğe göre baştan yapılandırır.
        """
        # Kağıt, marj ve gridi hesapla
        paper_w, paper_h = PAPER_SIZES[self.selected_paper_key]
        margin = int(self.margin_slider.get())
        
        self.current_grid_info = calculate_grid(paper_w, paper_h, margin)
        max_photos = self.current_grid_info['max_photos']
        
        if update_sliders:
            # Sığacak duruma göre UI Slider limitlerini güncelle
            if max_photos < 1:
                # Sığmıyorsa
                self.count_slider.configure(from_=0, to=0, number_of_steps=1)
                self.count_slider.set(0)
                self.count_label.configure(text=f"Adet (0):")
                self.max_count_label.configure(text="Bu boşlukla resim sığmıyor!", text_color="red")
            else:
                self.count_slider.configure(from_=1, to=max_photos, number_of_steps=max(1, max_photos-1))
                
                # Mevcut slider değeri max değerden büyükse aşağı çek
                curr_val = int(self.count_slider.get())
                if curr_val > max_photos:
                     self.count_slider.set(max_photos)
                     curr_val = max_photos
                elif curr_val == 0:
                     self.count_slider.set(1)
                     curr_val = 1
                     
                self.count_label.configure(text=f"Adet ({curr_val}):")
                self.max_count_label.configure(text=f"Max: {max_photos} adet sığabilir", text_color="gray")

        # Resmi çizme evresi
        if max_photos < 1:
            self.draw_preview(None)
            return

        selected_count = int(self.count_slider.get())
        
        # Sadece resim ve koordinatlar hazırsa oluştur
        if self.cropped_image and selected_count > 0:
             coords = get_coordinates(self.current_grid_info, selected_count, margin, center_align=True)
             self.current_canvas = generate_layout_canvas(paper_w, paper_h, self.cropped_image, coords)
             self.draw_preview(self.current_canvas)
        else:
             # Kağıt planı doğru ama resim seçilmemiş
             self.draw_preview(None)

    def draw_preview(self, canvas_img):
        """
        Tuvali küçültüp CTKImage ile arayüzdeki label'a giydirir.
        """
        if canvas_img is None:
            self.preview_label.configure(image=None, text="Canlı Önizleme\n\nResim seçildiğinde ve uygun alan olduğunda gösterilir.")
            return

        # Label in o anki boyutunu alıp, önizlemeyi o boyutta scale edebiliriz.
        # Basitlik açısından sabit max yükseklik 700 px baz alınır, aspect ratio korunur.
        preview_h = 700
        aspect_ratio = canvas_img.width / canvas_img.height
        preview_w = int(preview_h * aspect_ratio)

        preview_pil = get_preview_image(canvas_img, preview_w, preview_h)
        preview_ctk = ctk.CTkImage(light_image=preview_pil, dark_image=preview_pil, size=(preview_w, preview_h))

        self.preview_label.configure(image=preview_ctk, text="")
        # Garbage collector referans temizlemesin diye ufak bir atama engeli
        self.preview_label.image_ref = preview_ctk

    # --- Eylem (Action) Fonksiyonları ---

    def save_final_image(self):
        if not self.current_canvas:
            messagebox.showwarning("Uyarı", "Kaydedilecek geçerli bir önizleme (kanvas) yok. Lütfen resim seçin ve adet belirleyin.")
            return

        file_path = filedialog.asksaveasfilename(
            title="Yüksek Kalite Kaydet",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")]
        )
        if file_path:
            success = save_high_quality(self.current_canvas, file_path)
            if success:
                messagebox.showinfo("Başarılı", f"Dosya başarıyla 300 DPI kalitesinde kaydedildi:\n{file_path}")
            else:
                messagebox.showerror("Hata", "Dosya kaydedilirken bir hata oluştu.")

    def print_image(self):
        if not self.current_canvas:
            messagebox.showwarning("Uyarı", "Yazdırılacak bir önizleme (kanvas) yok. Lütfen resim seçin.")
            return

        # Geçici bir temp dosyası oluşturup işletim sistemine yolla
        temp_file = "print_temp.jpg"
        save_high_quality(self.current_canvas, temp_file)
        
        try:
            if platform.system() == "Windows":
                 # Windows için varsayılan uygulamadan yazdır
                 os.startfile(temp_file, "print")
            elif platform.system() == "Darwin":
                 # macOS için
                 subprocess.run(["open", "-a", "Preview", temp_file]) # macOS print ui can be triggered differently, preview opens it
            elif platform.system() == "Linux":
                 # Linux için (lp, xdg-open) - genelde varsayılan viewer'ı açmak pratik
                 subprocess.run(["xdg-open", temp_file])
            
            messagebox.showinfo("Baskı", "Baskı emri (veya önizleme penceresi) sisteminize gönderildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Yazdırma işlemi başarısız: {e}\n\nLütfen önce 'Kaydet' yapıp elle yazdırmayı deneyin.")


if __name__ == "__main__":
    app = PhotoPrintApp()
    app.mainloop()
