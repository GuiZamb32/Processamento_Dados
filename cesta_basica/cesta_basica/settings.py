BOT_NAME = "cesta_basica"

SPIDER_MODULES = ["cesta_basica.spiders"]
NEWSPIDER_MODULE = "cesta_basica.spiders"

ADDONS = {}

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

    
FEED_EXPORT_ENCODING = "utf-8"
