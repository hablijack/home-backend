#!/usr/bin/env python3
import hashlib
from argparse import ArgumentParser
from typing import Optional

from PIL import Image
from PIL import ImageEnhance
from PIL import ImageOps


def resize_image(image, width, height, fit=False):
    im = image.copy()
    if fit:
        im = ImageOps.pad(im, (width, height), color=(255, 255, 255))
    else:
        im = ImageOps.fit(im, (width, height))
    return im


def convert_image(
    infile: str,
    outfile: str,
    max_width: int,
    max_height: int,
    brightness: Optional[float] = None,
    fit: bool = False,
    dither: bool = False,
    show: bool = False,
) -> str:
    im = Image.open(infile)

    im = resize_image(im, max_width, max_height, fit)

    if brightness:
        im = ImageEnhance.Contrast(im).enhance(1 / brightness)
        im = ImageEnhance.Brightness(im).enhance(brightness)

    im = im.convert(mode="1" if dither else "L")

    if show:
        im.show()

    im = im.rotate(90, Image.NEAREST, expand=True)

    contents = []

    # Write out the output file.
    for y in range(0, im.size[1]):
        value = 0
        done = True
        for x in range(0, im.size[0]):
            pixel = im.getpixel((x, y))
            if x % 2 == 0:
                value = pixel >> 4
                done = False
            else:
                value |= pixel & 0xF0
                contents.append(value.to_bytes(1, "little"))
                done = True
        if not done:
            contents.append(value.to_bytes(1, "little"))

    data = b"".join(contents)

    with open(outfile, "wb") as f:
        f.write(data)

    content_hash = hashlib.sha256(data).hexdigest()

    with open(outfile + ".sha", "wb") as f:
        f.write(content_hash.encode())

    return content_hash


def main():
    parser = ArgumentParser()
    parser.add_argument("INPUT")
    parser.add_argument("OUTPUT")
    parser.add_argument(
        "--maxw",
        help="the max width of the image",
        action="store",
        dest="max_width",
        default=540,
        type=int,
    )
    parser.add_argument(
        "--maxh",
        help="the max height of the image",
        action="store",
        dest="max_height",
        default=960,
        type=int,
    )
    parser.add_argument(
        "-b",
        "--brighten",
        help="increase brightness by the given factor",
        action="store",
        dest="brightness",
        type=float,
    )
    parser.add_argument(
        "-d",
        "--dither",
        help="render the image as dithered monochrome, rather than greyscale",
        action="store_true",
    )
    parser.add_argument(
        "-s", "--show", help="show the image when done", action="store_true"
    )
    parser.add_argument(
        "-f",
        "--fit",
        help="fit the image in the frame (default is to crop)",
        action="store_true",
    )

    args = parser.parse_args()

    print("Converting...")
    content_hash = convert_image(
        infile=args.INPUT,
        outfile=args.OUTPUT,
        max_width=args.max_width,
        max_height=args.max_height,
        brightness=args.brightness,
        fit=args.fit,
        dither=args.dither,
        show=args.show,
    )

    print(f"Done, wrote image with hash {content_hash}.")


if __name__ == "__main__":
    main()