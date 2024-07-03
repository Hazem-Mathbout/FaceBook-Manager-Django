# utils.py
import matplotlib.font_manager as fm

def list_system_fonts():
    font_paths = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    font_names = [fm.FontProperties(fname=font_path).get_name() for font_path in font_paths]
    return sorted(set(font_names))  # Return unique and sorted font names
