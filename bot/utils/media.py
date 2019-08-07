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

def get_text_position(position: str, image_size: Tuple[int, int], text_size: Tuple[int, int]):
    x = 5
    if position in 'ns':
        x = (image_size[0] - text_size[0]) // 2
    elif position in 'nese':
        x = image_size[0] - text_size[0] - 5

    y = 5
    if position in 'we':
        y = (image_size[1] - text_size[1]) // 2
    elif position in 'swse':
        y = image_size[1] - text_size[1] - 5

    return x, y


def watermark_text(in_image: IO or str or Path,
                   out_buffer: IO or str or Path,
                   text: str,
                   file_extension: str = None,
                   pos: Tuple[int, int] or str = None,
                   colour: Tuple[int, int, int] = None,
                   font_name: str = None,
                   font_size: int = None,
                   font_size_percentage: int = None):
    colour = colour or (0, 0, 0)
    if font_name and font_name not in available_fonts:
        raise KeyError(f'Font "{font_name}" not available')
    font_name = font_name or 'default'
    font_path = available_fonts.get(font_name, available_fonts['default'])['path']

    if not isinstance(out_buffer, (str, Path)) and not file_extension:
        raise AttributeError('If out_image is a Buffer file_extension must be set')

    photo = Image.open(in_image)
    drawing = ImageDraw.Draw(photo)

    if not font_size or font_size_percentage:
        font_size_percentage = font_size_percentage or 50
        fontsize = 1
        img_fraction = font_size_percentage / 100

        font = ImageFont.truetype(font_path, fontsize)
        while font.getsize(text)[0] < img_fraction * photo.size[0]:
            fontsize += 1
            font = ImageFont.truetype(font_path, fontsize)
        fontsize -= 1  # Fontsize shall be one less than defined fraction
        font = ImageFont.truetype(font_path, fontsize)
    else:
        font = ImageFont.truetype(font_path, font_size)

    real_pos = pos or (0, 0)
    align = 'left'
    if isinstance(pos, str):
        real_pos = get_text_position(pos, photo.size, drawing.multiline_textsize(text, font))
        if pos in 'ns':
            align = 'center'
        elif pos in 'nese':
            align = 'right'

    drawing.text(real_pos, text, fill=colour, font=font, align=align)
    photo.save(out_buffer, format='webp', lossless=True)

    if hasattr(out_buffer, 'seek'):
        out_buffer.seek(0)
