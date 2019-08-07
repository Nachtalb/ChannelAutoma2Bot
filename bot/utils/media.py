import sys
from pathlib import Path
from typing import Tuple, IO

from PIL import Image, ImageDraw, ImageFont

available_fonts = {
    'default': {
        'darwin': '/Library/Fonts/Arial.ttf',
        'linux': 'DejaVuSans.ttf',
    },
    'arial': {
        'darwin': '/Library/Fonts/Arial.ttf',
        'linux': 'Arial.ttf',
    }
}


def get_font_path(font_name: str):
    font_name = font_name or 'default'
    return available_fonts.get(font_name.lower(), {}).get(sys.platform)

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
    font_path = get_font_path(font_name)
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
