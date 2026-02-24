# main.py
import os
import platform
import subprocess
import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from PIL import Image, ImageTk, ImageWin

# Load window icon
icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

from config import PAPER_SIZES, DEFAULT_MARGIN, PHOTO_SIZES
from layout_engine import calculate_grid, get_coordinates
from image_processor import load_and_crop_image, apply_manual_crop, generate_layout_canvas, get_preview_image, save_high_quality

# Görünüm ayarları
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class PhotoPrintApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Fotoğraf Baskı Yerleşim Otomasyonu")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # Set window icon
        if os.path.exists(icon_path):
            try:
                icon_photo = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, icon_photo)
            except Exception:
                pass

        # Durum değişkenleri
        self.selected_image_path = None
        # Orijinal resim (kırpma arayüzü için) ve kırpılmış resim
        self.original_image_pil = None
        self.cropped_image = None
        self.current_crop_box = None # (left, top, right, bottom) orijinal resim üzerindeki alan
        self.current_canvas = None # Gerçek 300DPI tuval resmi
        
        self.paper_keys = list(PAPER_SIZES.keys())
        self.selected_paper_key = self.paper_keys[0] # Varsayılan: ilk kağıt
        
        self.photo_keys = list(PHOTO_SIZES.keys())
        self.selected_photo_key = self.photo_keys[0] # Varsayılan: ilk fotoğraf boyutu
        
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
        self.img_btn = ctk.CTkButton(self.left_frame, text="Vesikalık Resim Seç", command=self.select_image, 
                                     height=50, font=ctk.CTkFont(size=15, weight="bold"))
        self.img_btn.pack(pady=10, padx=20, fill="x")

        self.img_status_label = ctk.CTkLabel(self.left_frame, text="Henüz resim seçilmedi", font=ctk.CTkFont(size=12, slant="italic"))
        self.img_status_label.pack(pady=(0, 10))

        # --- Kırpma Araçları ---
        self.crop_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.crop_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.crop_frame.grid_columnconfigure(0, weight=1)
        self.crop_frame.grid_columnconfigure(1, weight=1)
        
        self.manual_crop_btn = ctk.CTkButton(self.crop_frame, text="Manuel Kırp", command=self.open_manual_crop_ui, state="disabled")
        self.manual_crop_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        self.auto_crop_btn = ctk.CTkButton(self.crop_frame, text="Otomatik Kırp", command=self.apply_auto_crop, state="disabled")
        self.auto_crop_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # --- Fotoğraf Boyutu ---
        self.photo_size_label = ctk.CTkLabel(self.left_frame, text="Fotoğraf Ebadı:")
        self.photo_size_label.pack(anchor="w", padx=20)

        self.photo_combo = ctk.CTkComboBox(self.left_frame, values=self.photo_keys, command=self.update_photo_selection)
        self.photo_combo.set(self.selected_photo_key)
        self.photo_combo.pack(pady=(5, 15), padx=20, fill="x")

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

        # --- Adet Girişi ---
        self.count_label = ctk.CTkLabel(self.left_frame, text="Adet:")
        self.count_label.pack(anchor="w", padx=20)

        self.count_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.count_frame.pack(pady=(5, 5), padx=20, fill="x")

        self.minus_btn = ctk.CTkButton(self.count_frame, text="-", width=40, font=ctk.CTkFont(size=20, weight="bold"), command=self.decrement_count)
        self.minus_btn.pack(side="left")

        self.count_entry = ctk.CTkEntry(self.count_frame, width=80, justify="center", font=ctk.CTkFont(size=14))
        self.count_entry.insert(0, "1")
        self.count_entry.bind("<KeyRelease>", self.on_count_change_from_entry)
        self.count_entry.pack(side="left", padx=10)

        self.plus_btn = ctk.CTkButton(self.count_frame, text="+", width=40, font=ctk.CTkFont(size=20, weight="bold"), command=self.increment_count)
        self.plus_btn.pack(side="left")

        self.max_count_label = ctk.CTkLabel(self.left_frame, text="Max: 1 adet sığabilir", text_color="gray", font=ctk.CTkFont(size=11))
        self.max_count_label.pack(pady=(0, 20), anchor="w", padx=20)
        
        # --- İşlem Butonları (Kaydet / Yazdır) ---
        # Önce alt buton çerçevesini yerleştiriyoruz, böylece spacer tüm boşluğu kaplamadan alt taraf garantiye alınır
        self.action_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.action_frame.pack(side="bottom", fill="x", pady=20, padx=20)
        
        self.action_frame.grid_columnconfigure(0, weight=1)
        self.action_frame.grid_columnconfigure(1, weight=1)

        self.save_btn = ctk.CTkButton(self.action_frame, text="Yüksek Kalite\nKaydet (JPG)", command=self.save_final_image, 
                                      fg_color="#2b7b46", hover_color="#1f5c34", height=60, font=ctk.CTkFont(size=14, weight="bold"))
        self.save_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.print_btn = ctk.CTkButton(self.action_frame, text="Sistemden\nYazdır", command=self.print_image, 
                                       fg_color="#1f538d", hover_color="#14375e", height=60, font=ctk.CTkFont(size=14, weight="bold"))
        self.print_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Alt bölme için boşluk (En son pack edilmeli ki kalan boşluğu doldursun)
        self.spacer = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        self.spacer.pack(side="top", fill="both", expand=True)

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
            
            # Orijinal resmi hafızaya al
            try:
                self.original_image_pil = Image.open(self.selected_image_path)
                if self.original_image_pil.mode != 'RGB':
                    self.original_image_pil = self.original_image_pil.convert('RGB')
                
                # Butonları aktif et
                self.manual_crop_btn.configure(state="normal")
                self.auto_crop_btn.configure(state="normal")
                
                # Yeni resim yüklendiğinde otomatik kırpmayı uygula
                self.apply_auto_crop()
            except Exception as e:
                messagebox.showerror("Hata", f"Resim yüklenemedi: {e}")

    def apply_auto_crop(self):
        """Kırpma işlemini iptal edip merkeze odaklı standart otomatik kırpmaya döner."""
        if not self.selected_image_path:
            return
            
        self.current_crop_box = None # Özel kırpmayı sıfırla
        
        target_w, target_h = PHOTO_SIZES[self.selected_photo_key]
        self.cropped_image = load_and_crop_image(self.selected_image_path, target_w, target_h)
        self.refresh_layout()

    def update_photo_selection(self, choice):
        self.selected_photo_key = choice
        
        # Boyut değişince de, eger manuel kırpma yoksa otomatik, varsa eski oran uymayacağı için tekrar merkeze kırp
        if self.selected_image_path:
            self.apply_auto_crop()
        else:
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
        
    def get_current_count(self):
        try:
            return int(self.count_entry.get())
        except ValueError:
            return 1

    def decrement_count(self):
        curr = self.get_current_count()
        if curr > 1:
            self.count_entry.delete(0, 'end')
            self.count_entry.insert(0, str(curr - 1))
            self.refresh_layout(update_sliders=False)

    def increment_count(self):
        curr = self.get_current_count()
        max_photos = getattr(self, 'current_max_photos', 1)
        if curr < max_photos:
            self.count_entry.delete(0, 'end')
            self.count_entry.insert(0, str(curr + 1))
            self.refresh_layout(update_sliders=False)

    def on_count_change_from_entry(self, event):
        if not self.count_entry.get().strip():
            return
        curr = self.get_current_count()
        max_photos = getattr(self, 'current_max_photos', 1)
        
        changed = False
        if curr > max_photos:
            curr = max_photos
            changed = True
        elif curr < 1:
            curr = 1
            changed = True
            
        if changed:
            self.count_entry.delete(0, 'end')
            self.count_entry.insert(0, str(curr))
            
        self.refresh_layout(update_sliders=False)

    def refresh_layout(self, update_sliders=True):
        """
        Giriş verilerine göre grid hesaplamalarını günceller
        Önizleme tuvalini çizer. update_sliders True ise max slider limitlerini
        matematiğe göre baştan yapılandırır.
        """
        # Kağıt, fotoğraf, marj ve gridi hesapla
        paper_w, paper_h = PAPER_SIZES[self.selected_paper_key]
        photo_w, photo_h = PHOTO_SIZES[self.selected_photo_key]
        margin = int(self.margin_slider.get())
        
        self.current_grid_info = calculate_grid(paper_w, paper_h, photo_w, photo_h, margin)
        max_photos = self.current_grid_info['max_photos']
        self.current_max_photos = max_photos
        
        if update_sliders:
            if max_photos < 1:
                self.count_entry.delete(0, 'end')
                self.count_entry.insert(0, "0")
                self.minus_btn.configure(state="disabled")
                self.plus_btn.configure(state="disabled")
                self.count_entry.configure(state="disabled")
                self.max_count_label.configure(text="Bu boşlukla resim sığmıyor!", text_color="red")
            else:
                self.minus_btn.configure(state="normal")
                self.plus_btn.configure(state="normal")
                self.count_entry.configure(state="normal")
                
                try:
                    curr_val = int(self.count_entry.get())
                except ValueError:
                    curr_val = max_photos

                if getattr(self, 'last_max_photos', 0) == 0:
                    curr_val = max_photos
                else:
                    if curr_val > max_photos:
                         curr_val = max_photos
                    elif curr_val < 1:
                         curr_val = 1

                self.last_max_photos = max_photos
                
                self.count_entry.delete(0, 'end')
                self.count_entry.insert(0, str(curr_val))
                self.max_count_label.configure(text=f"Max: {max_photos} adet sığabilir", text_color="gray")

        # Resmi çizme evresi
        if max_photos < 1:
            self.draw_preview(None)
            return

        selected_count = self.get_current_count()
        
        # Sadece resim ve koordinatlar hazırsa oluştur
        if self.cropped_image and selected_count > 0:
             coords = get_coordinates(self.current_grid_info, photo_w, photo_h, selected_count, margin, center_align=True)
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

    # --- Kırpma (Crop) Arayüzü ---
    
    def open_manual_crop_ui(self):
        if not self.original_image_pil:
            return

        crop_win = ctk.CTkToplevel(self)
        crop_win.title("Manuel Kırpma Aracı")
        crop_win.geometry("800x600")
        crop_win.transient(self) # Ana pencereye bağla

        # Ekranı hazırla
        target_w, target_h = PHOTO_SIZES[self.selected_photo_key]
        target_ratio = target_w / target_h

        # Görüntü boyutunu ekrana sığacak şekilde ölçekle (Örn: max 500 yüksekliğinde)
        orig_w, orig_h = self.original_image_pil.size
        display_h = 500
        scale_factor = display_h / orig_h
        display_w = int(orig_w * scale_factor)

        display_pil = self.original_image_pil.resize((display_w, display_h), Image.Resampling.LANCZOS)
        display_img = ImageTk.PhotoImage(display_pil)
        
        # Onayla ve İptal Buton Çerçevesi (Pack olayında önce ekleyelim ki alta sabitlensin ve boşluk kalmamasına karşı güvende olsun)
        btn_frame = ctk.CTkFrame(crop_win, fg_color="transparent")
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        def save_crop():
            cx1, cy1, cx2, cy2 = cvs.coords(rect_id)
            # Gerçek resim koordinatlarına çevir
            real_x1 = cx1 / scale_factor
            real_y1 = cy1 / scale_factor
            real_x2 = cx2 / scale_factor
            real_y2 = cy2 / scale_factor
            
            self.current_crop_box = (int(real_x1), int(real_y1), int(real_x2), int(real_y2))
            
            # Kırpmayı uygula
            self.cropped_image = apply_manual_crop(self.selected_image_path, self.current_crop_box, target_w, target_h)
            self.refresh_layout()
            crop_win.destroy()

        ok_btn = ctk.CTkButton(btn_frame, text="Onayla", command=save_crop, fg_color="#2b7b46", hover_color="#1f5c34")
        ok_btn.pack(side="right", padx=5)
        cancel_btn = ctk.CTkButton(btn_frame, text="İptal", command=crop_win.destroy, fg_color="#a83232", hover_color="#7a2424")
        cancel_btn.pack(side="right", padx=5)

        # Tkinter Canvas (Üstte kalan tüm boşluğu doldursun)
        import tkinter as tk
        canvas_frame = ctk.CTkFrame(crop_win)
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        cvs = tk.Canvas(canvas_frame, width=display_w, height=display_h, bg="gray", highlightthickness=0)
        cvs.pack(anchor="center")
        cvs.create_image(0, 0, anchor="nw", image=display_img)
        cvs.image_ref = display_img # Garbage collector

        # Başlangıç kırpma kutusu
        box_w = int(display_w * 0.8)
        box_h = int(box_w / target_ratio)
        if box_h > display_h * 0.8:
            box_h = int(display_h * 0.8)
            box_w = int(box_h * target_ratio)

        start_x = (display_w - box_w) // 2
        start_y = (display_h - box_h) // 2

        # Çerçeve çizimi
        rect_id = cvs.create_rectangle(start_x, start_y, start_x + box_w, start_y + box_h, outline="red", width=3, dash=(5, 5))

        # Kontrolcü sınıfı (Fare işlemleri için)
        class CropController:
            def __init__(self, canvas, rect, aspect_ratio, max_w, max_h):
                self.canvas = canvas
                self.rect = rect
                self.ratio = aspect_ratio
                self.max_w = max_w
                self.max_h = max_h
                self.dragging = False
                self.resizing = False
                self.last_x = 0
                self.last_y = 0

            def on_press(self, event):
                x1, y1, x2, y2 = self.canvas.coords(self.rect)
                self.last_x = event.x
                self.last_y = event.y
                
                # Sağ alt köşeye yakınsa boyutlandır
                if (x2 - 15 <= event.x <= x2 + 15) and (y2 - 15 <= event.y <= y2 + 15):
                    self.resizing = True
                # İçindeyse taşı
                elif x1 < event.x < x2 and y1 < event.y < y2:
                    self.dragging = True

            def on_release(self, event):
                self.dragging = False
                self.resizing = False

            def on_motion(self, event):
                x1, y1, x2, y2 = self.canvas.coords(self.rect)
                dx = event.x - self.last_x
                dy = event.y - self.last_y

                if self.dragging:
                    # Sınır kontrolleriyle taşı
                    if x1 + dx < 0: dx = -x1
                    if y1 + dy < 0: dy = -y1
                    if x2 + dx > self.max_w: dx = self.max_w - x2
                    if y2 + dy > self.max_h: dy = self.max_h - y2
                    self.canvas.move(self.rect, dx, dy)
                    self.last_x += dx
                    self.last_y += dy

                elif self.resizing:
                    # Sınırla orantılı boyutlandır
                    new_w = (x2 - x1) + dx
                    new_h = new_w / self.ratio
                    
                    if x1 + new_w <= self.max_w and y1 + new_h <= self.max_h and new_w > 50:
                        self.canvas.coords(self.rect, x1, y1, x1 + new_w, y1 + new_h)
                        self.last_x = event.x
                        self.last_y = event.y

        controller = CropController(cvs, rect_id, target_ratio, display_w, display_h)
        cvs.bind("<ButtonPress-1>", controller.on_press)
        cvs.bind("<ButtonRelease-1>", controller.on_release)
        cvs.bind("<B1-Motion>", controller.on_motion)

        # Bilgi etiketi
        info = ctk.CTkLabel(crop_win, text="Çerçevenin içinden sürükleyerek taşıyın.\nSağ alt köşesinden sürükleyerek orantılı boyutlandırın.", text_color="gray")
        info.pack(side="bottom", pady=5)
        
        # Pencere tamamen çizildikten sonra odağı yakala (grab_set hatasını önlemek için)
        crop_win.after(100, crop_win.grab_set)


if __name__ == "__main__":
    app = PhotoPrintApp()
    app.mainloop()
