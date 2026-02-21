# image_processor.py
from PIL import Image, ImageOps

def load_and_crop_image(image_path, target_width, target_height):
    """
    Kullanıcının seçtiği resmi yükler ve akıllı kırpma (ortalayarak) ile 
    hedef boyutlara (target_width x target_height) getirir.
    LANCZOS filtresi ile yüksek kalite korunur.
    """
    try:
        img = Image.open(image_path)
        # Eğer resim RGB değilse RGB'ye çevir (örn. RGBA)
        if img.mode != 'RGB':
             img = img.convert('RGB')
             
        # ImageOps.fit ile resmi merkeze hizalayarak kırpıp boyutlandırıyoruz
        cropped_img = ImageOps.fit(
             img, 
             (target_width, target_height), 
             method=Image.Resampling.LANCZOS, 
             bleed=0.0, 
             centering=(0.5, 0.5)
        )
        return cropped_img
    except Exception as e:
        print(f"Resim işlenirken hata oluştu: {e}")
        return None

def apply_manual_crop(image_path, crop_box, target_width, target_height):
    """
    Orijinal resimden belirli bir dikdörtgen alanı (crop_box: left, top, right, bottom) kırpar 
    ve bu alanı nihai baskı boyutu olan target_width x target_height boyutuna ölçekler.
    """
    try:
        img = Image.open(image_path)
        if img.mode != 'RGB':
             img = img.convert('RGB')
             
        # Belirtilen alanı kırp
        cropped_region = img.crop(crop_box)
        
        # Kesilen bölgeyi asıl yüksek çözünürlüklü hedef baskı ebadına genişlet/küçült
        final_img = cropped_region.resize((target_width, target_height), Image.Resampling.LANCZOS)
        return final_img
    except Exception as e:
        print(f"Manuel kırpma uygulanırken hata: {e}")
        return None

def generate_layout_canvas(paper_width, paper_height, cropped_image, coordinates):
    """
    Belirtilen kağıt boyutlarında beyaz bir tuval oluşturur ve
    verilen koordinat listesine göre kırpılmış resmi tuvale yapıştırır.
    """
    # Beyaz arkaplanlı tuval (canvas) oluştur
    canvas = Image.new('RGB', (paper_width, paper_height), color='white')
    
    if cropped_image and coordinates:
        for (x, y) in coordinates:
             # Koordinatlara resmi yapıştır
             canvas.paste(cropped_image, (int(x), int(y)))
             
    return canvas

def get_preview_image(canvas, preview_width=None, preview_height=None):
    """
    Büyük (300 DPI) tuvali, UI'da (örn. sağ paneldeki alan) göstermek 
    için küçük bir önizleme (thumbnail) haline getirir.
    """
    # Önizleme için orijinal tuvali bozmayıp bir kopyası üzerinde çalışıyoruz
    preview = canvas.copy()
    
    # Standart bir UI önizleme boyutu
    if not preview_width or not preview_height:
        preview_width = 600
        preview_height = 800
        
    preview.thumbnail((preview_width, preview_height), Image.Resampling.LANCZOS)
    return preview

def save_high_quality(canvas, output_path):
    """
    Oluşturulan nihai tuvali disk üzerine 300 DPI olarak yüksek kalitede kaydeder.
    """
    try:
        # DPI bilgisiyle beraber kaydet
        canvas.save(output_path, dpi=(300, 300), quality=100)
        return True
    except Exception as e:
        print(f"Kaydetme hatası: {e}")
        return False
