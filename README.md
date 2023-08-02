# Tata-Soulfull-Scraper

- Description
  1. The scraper is used to scraper the Tata Soulfull Website.
  2. In order to use the scraper, download the required dependencies.
  3. Install the required dependencies with the help of pip install requirements.txt.
  4. Navigate to the foodScraper folder where 'scrapy.cfg' file is present.
  5. Dummy requests are fetched in the 'food_scraper.py' file from the 'product_requests' collection. Insert dummy requests into your own mongo collection from the "sample_requests.json" file.
  6. In the 'food_scraper.py' file, make sure to provide your own Mongo credentials in the mon_con, mon_db and mon_col variables.
  7. Run command `scrapy crawl food_scraper` in order to run the scraper.
