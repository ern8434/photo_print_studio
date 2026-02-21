# config.py

# 300 DPI için Standart Vesikalık/Biyometrik Boyutları (Genişlik x Yükseklik piksel olarak)
# Hesaplama: (cm / 2.54) * 300
PHOTO_SIZES = {
    'Biyometrik (5x6 cm)': (590, 708),
    'Standart Vesikalık (4.5x6 cm)': (531, 708),
    'Küçük Vesikalık (3.5x4.5 cm)': (413, 531),
    'Amerikan / Hindistan (5x5 cm)': (590, 590),
    'Geniş Vesikalık (6x9 cm)': (708, 1062)
}

# 300 DPI için Kağıt Boyutları (Genişlik x Yükseklik piksel olarak)
PAPER_SIZES = {
    '10x15 cm (4x6")': (1181, 1772),
    '13x18 cm (5x7")': (1535, 2126),
    '15x21 cm (6x8" - A5)': (1772, 2480),
    '20x25 cm (8x10")': (2362, 2953),
    '20x30 cm (8x12")': (2362, 3543),
    'A4 (21x29.7 cm)': (2480, 3508),
    'A3 (29.7x42 cm)': (3508, 4961)
}

# Varsayılan Margin Değeri (piksel)
DEFAULT_MARGIN = 50
