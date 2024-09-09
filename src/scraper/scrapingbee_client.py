
from scrapingbee import ScrapingBeeClient
from src.setting import api_settings
from src.utils.log import logging


class ScrapingClient:
    '''
    Handles API requests to ScrapingBee.

    Attributes:
    -----------
    api_key : str
        The API key for ScrapingBee.
    base_url : str
        The base URL for ScrapingBee API.
    '''

    def __init__(self):
        self.api_key = api_settings.SCRAPINGBEE_API_KEY
        self.client = ScrapingBeeClient(self.api_key)
        self.params = {
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
        logging.debug("ScrapingBee client initialized.")

    def get_images(self, web_url: str) -> list:
        '''
        Get all images from a web page.

        Returns:
        --------
        images : list
            A list of image URLs.
        '''
        try:
            scraped_img = []
            response = self.client.get(web_url, params=self.params)
            response.raise_for_status()

            response = response.json()
            images = response['all_images']
            logging.debug(f"Images from ScrapingBee: {len(images)}")
            if not images:
                raise Exception("No images found")
            for img in images:
                img_src = img.get('src') or img.get('data-src')
                if not img_src:
                    raise Exception("No image source found")
                full_img_url = f"{img_src}"
                scraped_img.append(full_img_url)
            logging.debug(f"Images scraped successfully: {len(scraped_img)}")
            return scraped_img

        except Exception as e:
            logging.error(f"Error getting images from ScrapingBee: {e}")
            raise Exception("Error getting images from ScrapingBee")
