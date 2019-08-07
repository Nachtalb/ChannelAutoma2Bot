import json
import sys
from pathlib import Path
from typing import IO, Tuple

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

available_fonts = {}
fonts_info_file = settings.AVAILABLE_FONTS

with open(fonts_info_file) as file:
    fonts_info = json.load(file)

for font_id, values in fonts_info.get(sys.platform, {}).items():
    try:
        ImageFont.truetype(values['path'], 14)
        available_fonts[font_id] = values
    except OSError:
        continue

if 'default' not in available_fonts:
    raise OSError('Default font not defined or not available')


def watermark_text(in_image: IO or str or Path,
                   out_buffer: IO or str or Path,
                   text: str,
                   file_extension: str = None,
                   pos: Tuple[int, int] = None,
                   colour: Tuple[int, int, int] = None,
                   font_name: str = None,
                   font_size: int = None):
    pos = pos or (0, 0)
    colour = colour or (0, 0, 0)
    if font_name and font_name not in available_fonts:
        raise KeyError(f'Font "{font_name}" not available')
    font_name = font_name or 'default'
    font_path = available_fonts.get(font_name, available_fonts['default'])['path']
    font_size = font_size or 20

    if not isinstance(out_buffer, (str, Path)) and not file_extension:
        raise AttributeError('If out_image is a Buffer file_extension must be set')

    photo = Image.open(in_image)
    drawing = ImageDraw.Draw(photo)

    font = ImageFont.truetype(font_path, font_size)

    drawing.text(pos, text, fill=colour, font=font)
    photo.save(out_buffer, format='webp', lossless=True)

    if hasattr(out_buffer, 'seek'):
        out_buffer.seek(0)
