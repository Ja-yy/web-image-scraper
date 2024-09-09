from src.extractor.image_extractor import ImageExtractor
from src.scraper.scrapingbee_client import ScrapingClient
from src.utils.log import logger
import argparse

def main(url: str, save_folder: str , min_area:int) -> None:
    '''
    Main function that orchestrates the image scraping and downloading process.

    Parameters:
    -----------
    url : str
        The webpage URL to scrape.
    save_folder : str
        The directory where images will be saved.
    api_key : str
        The ScrapingBee API key for making requests.
    '''
    # Initialize ScrapingBee client
    client = ScrapingClient()
    logger.info("Image scraper initialized.")
    # Initialize the image extractor and downloader
    extractor = ImageExtractor(
        client, min_pixel_size=min_area, base_folder=save_folder)

    # Extract image URLs
    image_urls = extractor.extract_image_info_as_json(url)
    logger.info(f"Found {len(image_urls)} images on the webpage.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Scrape images from a webpage using ScrapingBee.")
    parser.add_argument("url", help="URL of the webpage to scrape")
    parser.add_argument("-o", "--output", default="scraped_images",
                        help="Output folder for downloaded images")
    parser.add_argument("-m", "--min-area", type=int,
                        default=50000, help="Minimum image area in pixels")

    args = parser.parse_args()
    
    logger.info(f"Scraping images from {args.url}")
    main(args.url, args.output , args.min_area)
