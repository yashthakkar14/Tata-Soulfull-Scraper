import scrapy
from scrapy.selector import Selector
from pymongo import MongoClient
import json


class FoodScraperSpider(scrapy.Spider):
    name = 'food_scraper'

    def start_requests(self):
        mon_con = MongoClient('localhost', 27017)
        mon_db = mon_con['foodScraper']
        mon_col = mon_db['product_requests']
        mongo_requests = mon_col.find({})
        for request in mongo_requests:
            request_url = request.get('url')
            yield scrapy.Request(url = request_url, callback = self.parse)
    
    @staticmethod
    def get_key(data, key, default=None):
        value = data.get(key, default)
        if not value:
            value = default
        return value
    
    @staticmethod
    def clean_nutrition(value_list):
        final_value = ""
        for value in value_list:
            value = value.replace('\n', "")
            value = value.replace("\xa0", "")
            final_value += value
        return final_value
    
    def parse(self, response):
        product_script = response.xpath("//script[@type='application/ld+json']/text()").get()
        product_data = json.loads(product_script)
        title = self.get_key(product_data, 'name', None)
        display_image = self.get_key(product_data, 'image', None)
        images =  response.xpath('//img[@class="product-single__photo__img"]/@src').extract()
        description = response.xpath('//meta[@name="description"]/@content').extract()
        if description and description[0]:
            description = description[0]
            description = description.replace(" '", "")
        weight = self.get_key(product_data, 'weight', None)
        brand_dict = self.get_key(product_data, 'brand', None)
        brand = self.get_key(brand_dict, 'name', None)
        ingredients = None
        ingredients_string = response.xpath("//div[@id='acc-ingredients']/p/text()").extract()[0]
        if(ingredients_string):
            ingredients = ingredients_string.split(",")
        ingredients = [ingredient.strip() for ingredient in ingredients]
        price = None
        price_value = response.xpath('//meta[@property="og:price:amount"]/@content').extract()
        if price_value and price_value[0]:
            price = float(price_value[0])

        # Extracting Nutrition from the body
        nutrition_list = []

        table_headings = response.xpath('//table[@class="nutritionTable"]/thead/tr').extract()
        if table_headings and table_headings[0]:
            table_headings = table_headings[0]
        
        # Extracting gram_heading
        gram_heading = Selector(text=table_headings).xpath("//th").extract()[1]
        gram_heading_list = Selector(text=gram_heading).xpath("//text()").extract()
        gram_value = ""
        for gram_heading_value in gram_heading_list:
            gram_heading_value = gram_heading_value.replace("\xa0", "")
            gram_value += gram_heading_value
        
        # Extracting RDA heading
        rda_heading = Selector(text=table_headings).xpath("//th").extract()[2]
        rda_heading_list = Selector(text=rda_heading).xpath("//text()").extract()
        if rda_heading_list and rda_heading_list[0]:
            rda_value = rda_heading_list[0]

        table_values = response.xpath('//table[@class="nutritionTable"]/tbody/tr').extract()
        for table_value in table_values:
            nutrition_dict = {}
            table_value_elements = Selector(text=table_value).xpath("//td").extract()
            if table_value_elements:
                table_value_heading = table_value_elements[0]
                table_value_list = Selector(text=table_value_heading).xpath("//text()").extract()
                table_heading_value = self.clean_nutrition(table_value_list)
    
                table_value_gram = table_value_elements[1]
                table_value_gram = Selector(text=table_value_gram).xpath("//text()").extract()
                if table_value_gram and table_value_gram[0]:
                    table_value_gram = float(table_value_gram[0])
    
                table_rda_value = None
                table_value_rda = table_value_elements[2]
                table_value_rda = Selector(text=table_value_rda).xpath("//text()").extract()
                if table_value_rda and table_value_rda[0]:
                    table_rda_value = float(table_value_rda[0])
                
                nutrition_dict['nutrition_type'] = table_heading_value
                nutrition_dict[gram_value] = table_value_gram
                nutrition_dict[rda_value] = table_rda_value
    
                nutrition_list.append(nutrition_dict)
        
        item = {
            'title' : title,
            'display_image' : display_image,
            'images' : images,
            'description' : description,
            'weight' : weight,
            'brand' : brand,
            'ingredients' : ingredients,
            'price' : price,
            'nutrition' : nutrition_list
        }
            
        mon_con = MongoClient('localhost', 27017)
        mon_db = mon_con['foodScraper']
        mon_col = mon_db['product_details']
        mon_col.update_one({'title':title}, {"$set": item}, upsert=True)

        