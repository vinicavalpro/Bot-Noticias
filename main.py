import os
import logging
import requests
from datetime import datetime
from telegram import Bot
from telegram.ext import Application
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")


def buscar_noticias_financeiras():
    noticias = []
    if NEWS_API_KEY:
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {"category": "business", "language": "pt", "country": "br", "pageSize": 5, "apiKey": NEWS_API_KEY}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data.get("status") == "ok":
                for article in data.get("articles", [])[:5]:
                    titulo = article.get("title", "Sem titulo")
                    fonte = article.get("source", {}).get("name", "Fonte desconhecida")
                    url_artigo = article.get("url", "")
                    noticias.append(f"*{titulo}*\nFonte: {fonte}\n{url_artigo}")
        except Exception as e:
            logger.error(f"Erro: {e}")
    if not noticias:
        noticias = [
            "Mercado em destaque hoje - Acompanhe as variacoes do Ibovespa, dolar e juros.",
            "Dolar e cambio - Fique atento as movimentacoes do cambio.",
            "Politica monetaria - O Banco Central monitora a inflacao e pode ajustar a Selic.",
            "Bolsa de valores - Analistas recomendam diversificacao da carteira.",
            "Cenario internacional - Mercados globais influenciam a economia brasileira.",
        ]
    return noticias


async def enviar_noticias(bot: Bot):
    logger.info("Enviando noticias...")
    agora = datetime.now().strftime("%d/%m/%Y")
    noticias = buscar_noticias_financeiras()
    mensagem = f"NOTICIAS FINANCEIRAS DO DIA\nData: {agora}\n\n"
    for noticia in noticias:
        mensagem += f"{noticia}\n\n"
    mensagem += "Bot de Noticias Financeiras"
    try:
        await bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown", disable_web_page_preview=False)
        logger.info("Enviado com sucesso!")
    except Exception as e:
        logger.error(f"Erro ao enviar: {e}")


async def main():
    if not TOKEN:
        raise ValueError("TOKEN nao encontrado!")
    if not CHAT_ID:
        raise ValueError("CHAT_ID nao encontrado!")
    logger.info("Bot rodando...")
    app = Application.builder().token(TOKEN).build()
    bot = app.bot
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(enviar_noticias, trigger="cron", hour=9, minute=0, args=[bot], id="noticias_diarias")
    scheduler.start()
    logger.info("Agendador iniciado - envio diario as 9h Brasilia")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot encerrado.")
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
