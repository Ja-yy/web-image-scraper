import urllib.parse
import os
import hashlib
import json
from typing import List, Dict
from PIL import Image, UnidentifiedImageError
from src.utils.log import logger
from io import BytesIO
import requests
import magic
from contextlib import contextmanager
import cairosvg
from pillow_avif import AvifImagePlugin
import pillow_heif

# Register HEIC and AVIF support
pillow_heif.register_heif_opener()


class ImageExtractor:
    def __init__(self, client, min_pixel_size: int, base_folder: str = "images") -> None:
        self.client = client
        self.min_pixel_size = min_pixel_size
        self.base_folder = base_folder

        # Centralized extension to MIME type mapping
        self.extension_to_mime = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".avif": "image/avif",
            ".heic": "image/heic",
            ".jxl": "image/jxl",
            ".gif": "image/gif",
        }

        self.mime_to_ext = {v: k[1:]
                            for k, v in self.extension_to_mime.items()}

        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)

        # Initialize python-magic for MIME detection
        self.mime_detector = magic.Magic(mime=True)

    def is_supported_mime(self, mime_type: str) -> bool:
        ''' Check if MIME type is supported using the centralized dictionary '''
        return mime_type in self.extension_to_mime.values()

    def guess_mime_type_from_extension(self, image_url: str) -> str:
        ''' Guess MIME type from the file extension '''
        ext = os.path.splitext(image_url)[1].lower()
        return self.extension_to_mime.get(ext, "application/octet-stream")

    def get_absolute_url(self, base_url: str, image_url: str) -> str:
        ''' Convert relative URL to absolute URL if necessary. '''
        parsed_url = urllib.parse.urlparse(image_url)
        if parsed_url.scheme:
            return image_url
        else:
            return urllib.parse.urljoin(base_url, image_url)

    def get_mime_type(self, image_data: bytes, headers, image_url: str) -> str:
        ''' Detect MIME type using headers, python-magic, and file extension '''
        mime_type = headers.get('Content-Type')
        if mime_type:
            mime_type = mime_type.split(';')[0]
        if mime_type and mime_type != "application/octet-stream":
            return mime_type

        mime_type = self.mime_detector.from_buffer(image_data)
        if mime_type == "application/octet-stream":
            mime_type = self.guess_mime_type_from_extension(image_url)

        return mime_type

    def save_image(self, img_data: bytes, ext: str, folder_path: str) -> str:
        ''' Save the image file with MD5 hash as its name '''
        img_name = hashlib.md5(img_data).hexdigest()
        img_path = os.path.join(folder_path, f"{img_name}.{ext}")
        with open(img_path, 'wb') as f:
            f.write(img_data)
        logger.info(f"Image saved at: {img_path}")
        return img_path

    def save_json(self, image_info: Dict[str, str], folder_path: str) -> None:
        ''' Save the JSON file with the same name as the image in the same folder '''
        json_name = image_info["file_name"].rsplit('.', 1)[0] + '.json'
        json_path = os.path.join(folder_path, json_name)
        with open(json_path, 'w') as json_file:
            json.dump(image_info, json_file, indent=4)
        logger.info(f"JSON saved at: {json_path}")

    @contextmanager
    def download_image(self, image_url: str):
        ''' Download images from the provided URLs as a context manager. '''
        try:
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                yield response.content, response.headers
            else:
                logger.error(f"Failed to download image: {image_url}")
                yield None, None
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            yield None, None

    def process_image(self, image_data: bytes, mime_type: str, image_url: str, folder_path: str) -> str:
        ''' Process and verify if the image is valid and save it based on its MIME type '''
        try:
            if mime_type == "image/svg+xml":
                return self.handle_svg(image_data, image_url, folder_path)
            else:
                return self.handle_original_image(image_data, mime_type, image_url, folder_path)
        except Exception as e:
            logger.error(f"Error processing image: {image_url}, Error: {e}")
        return None

    def handle_original_image(self, image_data: bytes, mime_type: str, image_url: str, folder_path: str) -> str:
        ''' Handle images by saving the original image if it meets the pixel condition '''
        try:
            img = Image.open(BytesIO(image_data))
            img.load()
            if img.size[0] * img.size[1] >= self.min_pixel_size:
                ext = self.mime_to_ext.get(mime_type, "jpg")
                return self.save_image(image_data, ext, folder_path)
            else:
                logger.info(
                    f"Image size is less than {self.min_pixel_size} pixels: {image_url}")
        except UnidentifiedImageError:
            logger.error(
                f"UnidentifiedImageError: Cannot identify image: {image_url}")
        return None

    def handle_svg(self, image_data: bytes, image_url: str, folder_path: str) -> str:
        ''' Handle SVG files by converting them to PNG and saving '''
        try:
            img_name = hashlib.md5(image_data).hexdigest()
            output_png_path = os.path.join(folder_path, f"{img_name}.png")
            cairosvg.svg2png(bytestring=image_data, write_to=output_png_path)
            logger.info(f"SVG converted to PNG: {output_png_path}")
            return output_png_path
        except Exception as e:
            logger.error(
                f"Error processing SVG image: {image_url}, Error: {e}")
        return None

    def create_folder_for_url(self, url: str) -> str:
        ''' Create a folder based on the MD5 hash of the webpage URL '''
        folder_name = hashlib.md5(url.encode()).hexdigest()
        folder_path = os.path.join(self.base_folder, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path

    def extract_valid_image(self, url: str) -> List[str]:
        ''' Extracts image URLs from the webpage content. '''
        images = self.client.get_images(url)
        base_url = urllib.parse.urlparse(
            url).scheme + "://" + urllib.parse.urlparse(url).netloc
        valid_images = []

        # Create a folder based on the webpage URL
        folder_path = self.create_folder_for_url(url)

        for image_url in images:
            full_image_url = self.get_absolute_url(base_url, image_url)
            with self.download_image(full_image_url) as (image_data, headers):
                if image_data:
                    mime_type = self.get_mime_type(
                        image_data, headers, full_image_url)
                    if not self.is_supported_mime(mime_type):
                        logger.info(
                            f"Skipping unsupported image format: {mime_type} for URL: {full_image_url}")
                        continue

                    image_path = self.process_image(
                        image_data, mime_type, full_image_url, folder_path)
                    if image_path:
                        valid_images.append(image_path)

        return valid_images

    def extract_image_info_as_json(self, url: str) -> List[Dict[str, str]]:
        ''' Extract valid image information and return as a JSON object '''
        images = self.client.get_images(url)
        base_url = urllib.parse.urlparse(
            url).scheme + "://" + urllib.parse.urlparse(url).netloc
        image_info_list = []

        # Create a folder based on the webpage URL
        folder_path = self.create_folder_for_url(url)

        for image_url in images:
            full_image_url = self.get_absolute_url(base_url, image_url)
            with self.download_image(full_image_url) as (image_data, headers):
                if image_data:
                    mime_type = self.get_mime_type(
                        image_data, headers, full_image_url)
                    if not self.is_supported_mime(mime_type):
                        logger.info(
                            f"Skipping unsupported image format: {mime_type} for URL: {full_image_url}")
                        continue

                    image_path = self.process_image(
                        image_data, mime_type, full_image_url, folder_path)
                    logger.info(f"Image path: {image_path}")
                    if image_path:
                        image_info = {
                            "image_url": full_image_url,
                            "file_name": os.path.basename(image_path),
                            "mime_type": mime_type,
                            "path": image_path
                        }
                        # Save JSON for each valid image
                        self.save_json(image_info, folder_path)
                        logger.info(
                            f"Image info saved as JSON at: {folder_path}")
                        image_info_list.append(image_info)

        return image_info_list
