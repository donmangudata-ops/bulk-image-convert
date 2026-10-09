# bulk-image-convert

A small command line tool that converts and compresses images. It runs on your machine with Pillow. It needs no account and no key.

It reads JPG, PNG, WebP, AVIF, GIF, TIFF and BMP, and HEIC if you install the optional extra. It writes WebP, AVIF, JPEG or PNG and prints how many bytes you saved.

## Install

    pip install "git+https://github.com/donmangudata-ops/bulk-image-convert"
    pip install "bulk-image-convert[heic] @ git+https://github.com/donmangudata-ops/bulk-image-convert"   # optional, adds HEIC input

AVIF output needs a Pillow build with AVIF support (Pillow 11.3 or newer on most platforms).

## Local examples

Convert one file to WebP:

    bulk-image-convert photo.jpg

Convert a whole folder to JPEG at quality 70, resized to 1200 px wide:

    bulk-image-convert ./photos -f jpeg -q 70 --max-width 1200 -o ./small

Include sub folders, keep the same format:

    bulk-image-convert ./site-images -r -f same -q 75

Output goes to `./converted` unless you set `-o`. Your originals are never changed. Metadata such as GPS is removed. Photos are rotated upright using their orientation tag.

Use it from Python:

    from bulk_image_convert import convert_file
    r = convert_file("photo.jpg", "out", fmt="webp", quality=80, max_width=1600)
    print(r.saved)

## Need to convert thousands of image URLs? Use cloud mode

Local mode is the right tool for files on your disk. For large lists of image URLs you may want cloud runs, scheduling, or no load on your own machine. Cloud mode sends the same options to a hosted Apify Actor.

    pip install "bulk-image-convert[cloud] @ git+https://github.com/donmangudata-ops/bulk-image-convert"
    export APIFY_TOKEN=your_token
    bulk-image-convert --cloud https://example.com/a.jpg https://example.com/b.png -f webp -q 80

You use your own Apify account and token. Find it at https://console.apify.com/settings/integrations. The tool starts the run, waits, and downloads the converted files. Failed images are listed with a reason.

The Actor page has the current price and all options: https://apify.com/conserving_celerytop/image-converter-compressor

## Disclosure

The author of this package also built and runs the Apify Actor used by cloud mode. Local mode does not depend on it.

## Tests

    pip install -e ".[dev]"
    pytest

## License

MIT
