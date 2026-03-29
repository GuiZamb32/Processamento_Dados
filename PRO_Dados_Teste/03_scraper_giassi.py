import re
import scrapy
import json

# 1. Termos que devem ser ignorados para evitar falsos positivos
TERMOS_PROIBIDOS = [
    "zero_acucar", "biscoito", "bolacha", "bebida", "energetico", 
    "refrigerante", "esmalte", "pet", "cachorro", "gato", "bala", 
    "goma", "pastilha", "gelatina", "mistura_para", "bolo", "achocolatado"
]

# 2. Filtros específicos baseados nos slugs das URLs
FILTROS = {
    "arroz_polido": "Arroz", "arroz_parboilizado": "Arroz", "arroz_branco": "Arroz", "arroz_integral": "Arroz",
    "feijao_preto": "Feijão", "feijao_carioca": "Feijão", "feijao_vermelho": "Feijão",
    "oleo_de_soja": "Óleo de Soja",
    "acucar_refinado": "Açúcar", "acucar_cristal": "Açúcar", "acucar_demerara": "Açúcar",
    "cafe_torrado": "Café", "cafe_moido": "Café", "cafe_em_po": "Café", "cafe_vacuo": "Café",
    "macarrao_de_semola": "Macarrão", "macarrao_com_ovos": "Macarrão", "macarrao_espaguete": "Macarrão",
    "macarrao_parafuso": "Macarrão", "macarrao_penne": "Macarrão",
    "farinha_de_trigo": "Farinha", "sal_refinado": "Sal", "sal_iodado": "Sal",
}

RE_VOLUME = re.compile(r"(\d+[\.,]?\d*)\s*(kg|g|ml|l|litro|litros)\b", re.IGNORECASE)

def extrair_volume(texto: str):
    if not texto: return None, None
    match = RE_VOLUME.search(texto)
    if not match: return None, None
    valor = float(match.group(1).replace(",", "."))
    unid = match.group(2).lower()
    if unid == "g": return valor / 1000, "kg"
    if unid == "ml": return valor / 1000, "L"
    if unid in ("litro", "litros"): return valor, "L"
    return valor, unid

class GiassiCestaSpider(scrapy.Spider):
    name = "giassi_cesta"
    start_urls = ["https://www.giassi.com.br/sitemap.xml"]

    custom_settings = {
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "scrapy-giassi.log",
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": "cache",
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 2,
        "FEEDS": {
            "produtos_cesta.json": { # Alterado para o nome que o seu script 04 espera
                "format": "json",
                "encoding": "utf-8",
                "indent": 4,
                "overwrite": True,
            }
        },
    }

    def parse(self, response):
        response.selector.remove_namespaces()
        sub_sitemaps = response.xpath("//sitemap/loc[contains(text(), 'product')]/text()").getall()
        for url in sub_sitemaps:
            yield response.follow(url, self.parse_sitemap_produtos)

    def parse_sitemap_produtos(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").getall()
        for url in urls:
            url_lower = url.lower()
            if "/p" in url_lower:
                if any(termo in url_lower for termo in TERMOS_PROIBIDOS):
                    continue
                for slug, categoria in FILTROS.items():
                    if slug in url_lower:
                        yield response.follow(url, self.parse_produto, cb_kwargs={"categoria": categoria})
                        break

    def parse_produto(self, response, categoria):
        # Captura de dados via JSON-LD (Altamente recomendado para VTEX)
        js_data = response.xpath('//script[@type="application/ld+json"]/text()').get()
        
        if js_data:
            try:
                data = json.loads(js_data)
                # O JSON-LD pode ser uma lista ou um objeto único
                if isinstance(data, list): data = data[0]
                
                nome = data.get('name', '')
                preco = data.get('offers', {}).get('lowPrice') or data.get('offers', {}).get('price')
                
                if nome and preco and float(preco) > 0:
                    volume, unidade = extrair_volume(nome)
                    if volume:
                        yield {
                            "categoria": categoria,
                            "nome": nome,
                            "preco": float(preco),
                            "volume": f"{volume}{unidade}",
                            "preco_por_kg": round(float(preco) / volume, 2),
                            "url": response.url
                        }
            except Exception as e:
                self.logger.error(f"Erro ao processar JSON-LD em {response.url}: {e}")