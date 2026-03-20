import scrapy
from scrapy.selector import Selector
import w3lib.html

class CestaSpider(scrapy.Spider):
    name = "cesta_basica"
    start_urls = ["https://www.giassi.com.br/sitemap.xml"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'LOG_FILE': 'scrapy_output.log',
        'HTTPCACHE_ENABLED' : True,
        'HTTPCACHE_EXPIRATION_SECS' : 86400,
        'HTTPCACHE_DIR' : 'cache',
        'HTTPCACHE_IGNORE_HTTP_CODES' : [404, 500, 502, 503]
    }

    def parse(self, response: scrapy.http.Response):
        response.selector.remove_namespaces()
        sitemaps_produtos = response.xpath('//sitemap/loc[contains(text(),"/product")]/text()').getall()
        
        for url in sitemaps_produtos:
            # yield envia a requisição para o Scrapy processar
            yield response.follow(url, self.parse_lista_produtos)
            # return # Comente esta linha quando quiser rodar em todos os sitemaps
            break 

    def parse_lista_produtos(self, response: scrapy.http.Response):
        response.selector.remove_namespaces()
        
        # Filtra URLs de Arroz 1kg e Feijão (exemplo de expansão da lógica)
        urls_cesta = response.xpath(
            '//url/loc[contains(text(),"/arroz") and contains(text(),"1kg")]/text() | '
            '//url/loc[contains(text(),"/feijao")]/text()'
        ).getall()

        for url in urls_cesta:
            yield response.follow(url, self.parse_info_produtos)

    def parse_info_produtos(self, response: scrapy.http.Response):
        # Aqui extraímos os dados da página do produto
        # Os seletores abaixo são genéricos, você deve inspecionar o HTML do Giassi para validar
        yield {
            'nome': response.css('h1.product-name::text').get(),
            'preco': response.xpath('//span[contains(@class, "price")]/text()').get(),
            'url': response.url,
        }