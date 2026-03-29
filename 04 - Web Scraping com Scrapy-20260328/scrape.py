import scrapy
import w3lib.html


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
        "https://www.consorciofenix.com.br/sitemap.xml",
    ]

    @classmethod
    def update_settings(cls, settings):
        super().update_settings(settings)
        settings.set("BOT_NAME", "Pesquisa_Linhas_CFX", priority="spider")
    
    def parse(self, response: scrapy.http.Response):
        
        response.selector.remove_namespaces()
        horarios = response.xpath('//url/loc[contains(text(),"/horarios/")]/text()')
        print('Horarios: ')
        for url in horarios:
            if url is not None:
                yield response.follow(url, self.parse_details)

    def parse_details(self, response: scrapy.http.Response):
        
            response.selector.remove_namespaces()
            box = response.xpath('//div[@class="content-horarios-int"]')
            # dias = box.xpath('./div//button').getall()
            rows = box.xpath('//div[contains(@class,"row-horarios")]')
            line = response.xpath('//div[contains(@class,"content-horarios")]//h3').get()
            route = response.xpath('//div[contains(@class,"content-text-itinerario")]//li/text()').getall()        


            lineSchedule = {
                'linha':w3lib.html.remove_tags(line).replace('\u00a0','-'),
                'itinerario':route,
                'horarios':[],
            }

            for row in rows:
                partida = row.xpath("./preceding-sibling::div//h5/text()").get()
                info = row.xpath('./div[@data-semana]')
                dia = info.xpath('./@data-semana').get()
                horarios = info.xpath('./@data-horario').getall()
                schedule = {'partida':partida, 'day': dia, 'time': horarios}
                lineSchedule['horarios'].append(schedule)

            yield lineSchedule
            