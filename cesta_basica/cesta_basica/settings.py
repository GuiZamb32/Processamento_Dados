# Scrapy settings for cesta_basica project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "cesta_basica"

SPIDER_MODULES = ["cesta_basica.spiders"]
NEWSPIDER_MODULE = "cesta_basica.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "cesta_basica (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

    
FEED_EXPORT_ENCODING = "utf-8"
