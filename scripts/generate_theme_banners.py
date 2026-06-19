"""Generate theme-aware README banner assets.

By default this downloads the dark banner and creates a light-mode variant.
If you make a hand-edited light banner, pass it with --light-source and the
script will use that instead.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from urllib.request import urlopen

from PIL import Image


DEFAULT_DARK_SOURCE = (
    "https://github.com/user-attachments/assets/"
    "b06d2f51-5e14-47d1-9708-aa27f79ef677"
)


def save_source(source: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.startswith(("http://", "https://")):
        with urlopen(source) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
        return

    source_path = Path(source)
    if source_path.resolve() == destination.resolve():
        return

    shutil.copyfile(source_path, destination)


def make_light_banner(dark_path: Path, light_path: Path) -> None:
    image = Image.open(dark_path).convert("RGB")
    original = image.copy()
    width, height = image.size
    pixels = image.load()

    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            lightness = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
            saturation = max(r, g, b) - min(r, g, b)

            if lightness < 78:
                pixels[x, y] = (255, 255, 255)
            elif saturation < 72 and lightness > 118:
                pixels[x, y] = (0, 0, 0)

    # Restore the laptop/photo area from the original dark banner. The source
    # PNG is flattened, so preserving this measured circle is more reliable
    # than trying to classify individual photo pixels by color.
    photo_cx = width * (2923 / 3780)
    photo_cy = height * (1033 / 1890)
    photo_radius = min(width, height) * (665 / 1890)
    photo_radius_sq = photo_radius * photo_radius
    original_pixels = original.load()

    for y in range(height):
        dy_sq = (y - photo_cy) * (y - photo_cy)
        for x in range(width):
            if (x - photo_cx) * (x - photo_cx) + dy_sq <= photo_radius_sq:
                pixels[x, y] = original_pixels[x, y]

    light_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(light_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dark-source",
        default=DEFAULT_DARK_SOURCE,
        help="Dark banner URL or local file path.",
    )
    parser.add_argument(
        "--dark-out",
        default="assets/banner-dark.png",
        help="Where to write the dark banner.",
    )
    parser.add_argument(
        "--light-out",
        default="assets/banner-light.png",
        help="Where to write the light banner.",
    )
    parser.add_argument(
        "--light-source",
        help="Optional hand-edited light banner. If set, it is copied to --light-out.",
    )
    args = parser.parse_args()

    dark_out = Path(args.dark_out)
    light_out = Path(args.light_out)

    save_source(args.dark_source, dark_out)

    if args.light_source:
        light_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.light_source, light_out)
    else:
        make_light_banner(dark_out, light_out)

    print(f"Wrote {dark_out}")
    print(f"Wrote {light_out}")


if __name__ == "__main__":
    main()
