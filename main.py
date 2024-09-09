import os
import json
import argparse
from dotenv import load_dotenv
from scrapingbee import ScrapingBeeClient
import requests
from io import BytesIO
from urllib.parse import urljoin
from PIL import Image
import pillow_heif

# Register HEIF support
pillow_heif.register_heif_opener()

load_dotenv()

def get_api_key():
    api_key = os.getenv('SCRAPINGBEE_API_KEY')
    if not api_key:
        raise ValueError("SCRAPINGBEE_API_KEY not found in .env file")
    return api_key

def get_image_info(url):
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with Image.open(BytesIO(response.content)) as img:
                return img.format, img.size
    except Exception as e:
        print(f"Error getting image info for {url}: {str(e)}")
    return None, None

def download_image(url, folder, min_area):
    try:
        img_format, size = get_image_info(url)
        if img_format and size:
            width, height = size
            if width * height >= min_area:
                response = requests.get(url)
                if response.status_code == 200:
                    filename = os.path.join(folder, url.split('/')[-1].split('?')[0])
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded: {filename} (Size: {width}x{height}, Format: {img_format})")
                else:
                    print(f"Failed to download: {url}")
            else:
                print(f"Skipped (too small): {url} (Size: {width}x{height}, Format: {img_format})")
        else:
            print(f"Skipped (not an image or couldn't determine size): {url}")
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")

def scrape_images(url, output_folder, min_area):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    api_key = get_api_key()
    client = ScrapingBeeClient(api_key=api_key)

    params = {
        'render_js': True,
        'extract_rules': {
            "all_images": {
                "selector": "img",
                "type": "list",
                "output": {
                    "src": {
                        "selector": "img",
                        "output": "@src"
                    },
                    "data-src": {
                        "selector": "img",
                        "output": "@data-src"
                    }
                }
            }
        }
    }

    try:
        print("Sending request to ScrapingBee...")
        response = client.get(url, params=params)
        print(f"Response received. Status code: {response.status_code}")
        
        if response.ok:
            data = json.loads(response.content)
            print(f"Extracted data: {json.dumps(data, indent=2)}")
            
            img_urls = []
            for img in data.get('all_images', []):
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(url, src)
                    img_urls.append(full_url)
            
            print(f"Found {len(img_urls)} image URLs")
            
            for img_url in img_urls:
                print(f"Processing image: {img_url}")
                download_image(img_url, output_folder, min_area)
        else:
            print(f"Failed to scrape the website. Status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Scrape images from a webpage using ScrapingBee.")
    parser.add_argument("url", help="URL of the webpage to scrape")
    parser.add_argument("-o", "--output", default="scraped_images", help="Output folder for downloaded images")
    parser.add_argument("-m", "--min-area", type=int, default=50000, help="Minimum image area in pixels")
    
    args = parser.parse_args()

    print(f"Scraping images from: {args.url}")
    print(f"Saving to: {args.output}")
    print(f"Minimum image area: {args.min_area} pixels")

    scrape_images(args.url, args.output, args.min_area)

if __name__ == "__main__":
    main()