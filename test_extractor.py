from src.extractor.image_extractor import ImageExtractor
from src.scraper.scrapingbee_client import ScrapingClient

client = ScrapingClient()

img_ext = ImageExtractor(client=client, min_pixel_size=0)

# web_page_img = client.get_images(
#     "https://www.ai21.com/blog/the-promise-of-rag-bringing-enterprise-generative-ai-to-life")


valid_img = img_ext.extract_valid_image(
    "https://www.ai21.com/blog/the-promise-of-rag-bringing-enterprise-generative-ai-to-life")
