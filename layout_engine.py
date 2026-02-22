# layout_engine.py

def calculate_grid(paper_width, paper_height, photo_width, photo_height, margin, spacing=20):
    """
    Verilen kağıt boyutu ve marjlara göre sığabilecek max satır ve sütun sayısını hesaplar.
    """
    avail_width = paper_width - (2 * margin)
    avail_height = paper_height - (2 * margin)
    
    # Sütun sayısı hesaplama
    # Her resim + sağındaki boşluk (son resim hariç)
    # cols * photo_width + (cols - 1) * spacing <= avail_width
    # cols * (photo_width + spacing) - spacing <= avail_width
    
    cols = (avail_width + spacing) // (photo_width + spacing)
    rows = (avail_height + spacing) // (photo_height + spacing)
    
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

def get_coordinates(grid_info, photo_width, photo_height, selected_count, margin, center_align=True):
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
    if center_align:
        actual_cols = min(cols, selected_count)
        actual_rows = (selected_count + cols - 1) // cols
        
        total_grid_width = (actual_cols * photo_width) + ((actual_cols - 1) * spacing)
        total_grid_height = (actual_rows * photo_height) + ((actual_rows - 1) * spacing)
        
        start_x = margin + (grid_info['avail_width'] - total_grid_width) // 2
        start_y = margin + (grid_info['avail_height'] - total_grid_height) // 2
    else:
        # Basitçe sol üstten başla
        start_x = margin
        start_y = margin
    
    count = 0
    for row in range(rows):
        for col in range(cols):
            if count >= selected_count:
                break
            
            x = start_x + col * (photo_width + spacing)
            y = start_y + row * (photo_height + spacing)
            coords.append((x, y))
            count += 1
            
    return coords
