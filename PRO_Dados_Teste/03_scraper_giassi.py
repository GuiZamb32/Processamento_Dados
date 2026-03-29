"""
03_scraper_giassi.py
Spider Scrapy para extração dos produtos da cesta básica no site do Giassi (Florianópolis).
Focado em alta precisão para evitar itens irrelevantes (esmaltes, bebidas zero, pet shop).
"""

import re
import scrapy

# 1. Termos que devem ser ignorados para evitar falsos positivos
TERMOS_PROIBIDOS = [
    "zero_acucar", "biscoito", "bolacha", "bebida", "energetico", 
    "refrigerante", "esmalte", "pet", "cachorro", "gato", "bala", 
    "goma", "pastilha", "gelatina", "mistura_para", "bolo", "achocolatado"
]

# 2. Filtros específicos baseados nos slugs das URLs
FILTROS = {
    # ARROZ
    "arroz_polido": "Arroz",
    "arroz_parboilizado": "Arroz",
    "arroz_branco": "Arroz",
    "arroz_integral": "Arroz",
    
    # FEIJÃO
    "feijao_preto": "Feijão",
    "feijao_carioca": "Feijão",
    "feijao_vermelho": "Feijão",
    
    # ÓLEO
    "oleo_de_soja": "Óleo de Soja",
    
    # AÇÚCAR
    "acucar_refinado": "Açúcar",
    "acucar_cristal": "Açúcar",
    "acucar_demerara": "Açúcar",
    
    # CAFÉ
    "cafe_torrado": "Café",
    "cafe_moido": "Café",
    "cafe_em_po": "Café",
    "cafe_vacuo": "Café",
    
    # MACARRÃO
    "macarrao_de_semola": "Macarrão",
    "macarrao_com_ovos": "Macarrão",
    "macarrao_espaguete": "Macarrão",
    "macarrao_parafuso": "Macarrão",
    "macarrao_penne": "Macarrão",
    
    # FARINHA E SAL
    "farinha_de_trigo": "Farinha",
    "sal_refinado": "Sal",
    "sal_iodado": "Sal",
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
        "LOG_FILE": "scrapy-giassi.log",  # <--- Alteração solicitada aqui
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": "cache",
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 2,
        "FEEDS": {
            "produtos_raw.json": {
                "format": "json",
                "encoding": "utf-8",
                "indent": 4,
                "overwrite": True,
            }
        },
    }

    def parse(self, response):
        response.selector.remove_namespaces()
        # Captura apenas sitemaps que contêm produtos
        sub_sitemaps = response.xpath("//sitemap/loc[contains(text(), 'product')]/text()").getall()
        for url in sub_sitemaps:
            yield response.follow(url, self.parse_sitemap_produtos)

    def parse_sitemap_produtos(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").getall()
        
        for url in urls:
            url_lower = url.lower()
            
            # 1. Filtro de Segurança: Deve ser produto (/p)
            if "/p" in url_lower:
                # 2. Filtro Negativo: Ignora se tiver termo proibido
                if any(termo in url_lower for termo in TERMOS_PROIBIDOS):
                    continue
                
                # 3. Filtro Positivo: Verifica se bate com os nossos itens específicos
                for slug, categoria in FILTROS.items():
                    if slug in url_lower:
                        self.logger.info(f"Alvo encontrado: {url}")
                        yield response.follow(url, self.parse_produto, cb_kwargs={"categoria": categoria})
                        break

    def parse_produto(self, response, categoria):
        # Nome do produto (tentando seletores VTEX IO)
        nome = (
            response.css("h1 span::text").get() or 
            response.css(".vtex-store-components-3-x-productBrand::text").get() or 
            response.xpath("//title/text()").get() or
            ""
        ).strip()
        
        if not nome: return

        # Preço (Inteiro + Centavos)
        preco_inteiro = response.css(".vtex-product-price-1-x-currencyInteger::text").get()
        preco_fracao = response.css(".vtex-product-price-1-x-currencyFraction::text").get() or "00"
        
        if preco_inteiro:
            preco = float(f"{preco_inteiro.replace('.', '')}.{preco_fracao}")
        else:
            # Fallback para preço em texto corrido
            preco_txt = response.xpath("//*[contains(@class, 'Price')]//text()[contains(., 'R$')]").get()
            if not preco_txt: return
            preco = float(preco_txt.replace("R$", "").replace(".", "").replace(",", ".").strip())

        volume, unidade = extrair_volume(nome)
        if not volume: return

        yield {
            "categoria": categoria,
            "nome": nome,
            "preco": preco,
            "volume": f"{volume}{unidade}",
            "preco_por_kg": round(preco / volume, 2),
            "url": response.url
        }