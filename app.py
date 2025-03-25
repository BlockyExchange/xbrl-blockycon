#!/usr/bin/env pypy3
import os
import hashlib
import asyncio
from aiohttp import web

async def compute_hash(input_str: str) -> (str, int):
    # Compute MD5 hash asynchronously using a thread to avoid blocking the event loop.
    def do_hash():
        return hashlib.md5(input_str.encode('utf-8')).hexdigest()
    hash_str = await asyncio.to_thread(do_hash)
    hash_int = int(hash_str, 16)
    return hash_str, hash_int

async def list_image_files(image_dir: str, valid_extensions: set) -> list:
    # List files asynchronously using a thread.
    def list_files():
        return sorted([
            f for f in os.listdir(image_dir)
            if os.path.splitext(f)[1].lower() in valid_extensions
        ])
    return await asyncio.to_thread(list_files)

async def handle_request(request: web.Request) -> web.Response:
    input_string = request.match_info.get('input_string', '')
    _, hash_int = await compute_hash(input_string)

    image_dir = "./images"
    valid_extensions = {'.jpg', '.jpeg', '.png', '.gif'}
    try:
        image_files = await list_image_files(image_dir, valid_extensions)
    except FileNotFoundError:
        return web.Response(text="Images directory not found.", status=404)

    if not image_files:
        return web.Response(text="No images found in the images directory.", status=404)

    # Pick an image deterministically based on the hash.
    selected_image = image_files[hash_int % len(image_files)]
    selected_image_path = os.path.join(image_dir, selected_image)

    # Compute a hue shift percentage between 80 and 120 (100 means no change).
    hue_shift = 100 + (hash_int % 41 - 20)

    # Determine output format and MIME type based on file extension.
    ext = os.path.splitext(selected_image)[1].lower()
    if ext == '.png':
        out_format = "png:-"  # Output as PNG
        mime_type = "image/png"
    else:
        out_format = "jpg:-"  # Default to JPEG for other types
        mime_type = "image/jpeg"

    # Build the ImageMagick command. We'll run it asynchronously.
    cmd = [
        "convert",
        selected_image_path,
        "-modulate", f"100,100,{hue_shift}",
        out_format
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        error_message = stderr.decode() if stderr else "Unknown error"
        return web.Response(text=f"Error processing image: {error_message}", status=500)

    return web.Response(body=stdout, content_type=mime_type)

app = web.Application()
app.router.add_get("/{input_string}", handle_request)

if __name__ == '__main__':
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    web.run_app(app, host=host, port=port)
