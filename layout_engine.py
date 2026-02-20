# layout_engine.py
from config import PHOTO_WIDTH, PHOTO_HEIGHT

def calculate_grid(paper_width, paper_height, margin, spacing=20):
    """
    Verilen kağıt boyutu ve marjlara göre sığabilecek max satır ve sütun sayısını hesaplar.
    """
    avail_width = paper_width - (2 * margin)
    avail_height = paper_height - (2 * margin)
    
    # Sütun sayısı hesaplama
    # Her resim + sağındaki boşluk (son resim hariç)
    # cols * PHOTO_WIDTH + (cols - 1) * spacing <= avail_width
    # cols * (PHOTO_WIDTH + spacing) - spacing <= avail_width
    
    cols = (avail_width + spacing) // (PHOTO_WIDTH + spacing)
    rows = (avail_height + spacing) // (PHOTO_HEIGHT + spacing)
    
    # Negatif değerlere karşı güvenlik önlemi
    cols = max(0, cols)
    rows = max(0, rows)
    
    max_photos = cols * rows
    
    return {
        'cols': cols,
        'rows': rows,
        'max_photos': max_photos,
        'avail_width': avail_width,
        'avail_height': avail_height,
        'spacing': spacing
    }

def get_coordinates(grid_info, selected_count, margin, center_align=True):
    """
    Seçilen resim adedine göre (ızgara yerleşimindeki) (x, y) başlangıç koordinatlarını döndürür.
    center_align True ise dökümanı kağıdın ortasına (merkeze) hizalar.
    """
    coords = []
    cols = grid_info['cols']
    rows = grid_info['rows']
    spacing = grid_info['spacing']
    
    if cols == 0 or rows == 0 or selected_count == 0:
        return coords
        
    # Kağıt üstünde ızgarayı ortalamak için başlangıç ofsetini hesapla
    if center_align and selected_count == grid_info['max_photos']:
        total_grid_width = (cols * PHOTO_WIDTH) + ((cols - 1) * spacing)
        total_grid_height = (rows * PHOTO_HEIGHT) + ((rows - 1) * spacing)
        
        start_x = margin + (grid_info['avail_width'] - total_grid_width) // 2
        start_y = margin + (grid_info['avail_height'] - total_grid_height) // 2
    else:
        # Basitçe sol üstten başla
        start_x = margin
        start_y = margin
        
        # Eğer blok ortaya hizalanacaksa ve her satır eşit olacaksa
        if center_align:
             total_grid_width = (cols * PHOTO_WIDTH) + ((cols - 1) * spacing)
             start_x = margin + (grid_info['avail_width'] - total_grid_width) // 2
    
    count = 0
    for row in range(rows):
        for col in range(cols):
            if count >= selected_count:
                break
            
            x = start_x + col * (PHOTO_WIDTH + spacing)
            y = start_y + row * (PHOTO_HEIGHT + spacing)
            coords.append((x, y))
            count += 1
            
    return coords
