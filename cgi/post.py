"""Add bloom/glow to a rendered frame (cheap fake haze)."""
import sys
from PIL import Image, ImageFilter, ImageChops, ImageEnhance
im = Image.open(sys.argv[1]).convert("RGB")
glow = im.point(lambda v: max(0, v - 90) * 2)
g1 = glow.filter(ImageFilter.GaussianBlur(12))
g2 = glow.filter(ImageFilter.GaussianBlur(40))
out = ImageChops.screen(im, ImageChops.screen(g1, g2))
out = ImageEnhance.Contrast(out).enhance(1.08)
out.save(sys.argv[2])
