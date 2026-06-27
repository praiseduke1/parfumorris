import os
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import connection
from PIL import Image, ImageDraw, ImageFont

COLORS = [
    (52, 73, 94),
    (41, 128, 185),
    (39, 174, 96),
    (142, 68, 173),
    (231, 76, 60),
    (243, 156, 18),
    (26, 188, 156),
    (230, 126, 34),
    (149, 165, 166),
    (44, 62, 80),
    (22, 160, 133),
    (192, 57, 43),
    (155, 89, 182),
    (52, 152, 219),
    (46, 204, 113),
]


def make_placeholder(name, size=(280, 336), color_index=None):
    if color_index is None:
        color_index = abs(hash(name)) % len(COLORS)
    bg = COLORS[color_index]
    img = Image.new('RGB', size, color=bg)
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype('arial.ttf', 22)
        font_small = ImageFont.truetype('arial.ttf', 14)
    except (OSError, IOError):
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw perfume bottle icon (simple shape)
    bottle_color = (255, 255, 255, 40)
    bx, by = size[0] // 2 - 30, size[1] // 2 - 60
    draw.rectangle([bx, by + 20, bx + 60, by + 80], fill=bottle_color, outline=(255, 255, 255, 60))
    draw.rectangle([bx + 15, by, bx + 45, by + 20], fill=bottle_color, outline=(255, 255, 255, 60))
    draw.ellipse([bx + 20, by + 85, bx + 40, by + 100], fill=bottle_color)

    # Draw product name
    lines = []
    words = name.split()
    current = ''
    for w in words:
        test = f'{current} {w}'.strip()
        bbox = draw.textbbox((0, 0), test, font=font_small)
        if bbox[2] - bbox[0] > size[0] - 30:
            lines.append(current)
            current = w
        else:
            current = test
    lines.append(current)

    y_offset = size[1] // 2 + 30
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text(((size[0] - tw) // 2, y_offset), line, fill=(255, 255, 255), font=font_small)
        y_offset += 22

    # Draw decorative circles
    draw.ellipse([size[0] - 50, -20, size[0] + 20, 50], fill=(255, 255, 255, 15))
    draw.ellipse([-30, size[1] - 40, 40, size[1] + 10], fill=(255, 255, 255, 10))

    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


class Command(BaseCommand):
    help = 'Generate placeholder product images for products with missing media files'

    def handle(self, *args, **options):
        media_root = settings.MEDIA_ROOT
        products_dir = media_root / 'products'
        os.makedirs(products_dir, exist_ok=True)

        # Query products directly from DB to avoid model import issues
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, name, image FROM products_product WHERE image IS NOT NULL AND image != \'\'')
            products = cursor.fetchall()

        created = 0
        skipped = 0
        errors = 0

        for pk, name, image_path in products:
            if not image_path:
                continue

            fname = os.path.basename(image_path)
            target = products_dir / fname

            if target.exists():
                self.stdout.write(f'  [SKIP] {fname} — already exists')
                skipped += 1
                continue

            try:
                data = make_placeholder(name)
                with open(target, 'wb') as f:
                    f.write(data)
                self.stdout.write(f'  [OK]   {fname} — placeholder for "{name}"')
                created += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [FAIL] {fname} — {e}'))
                errors += 1

        total = created + skipped + errors
        self.stdout.write(self.style.SUCCESS(f'\nDone: {created} created, {skipped} skipped, {errors} errors, {total} total'))
