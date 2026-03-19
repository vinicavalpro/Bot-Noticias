import asyncio
import os
import requests
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

def buscar_noticias():
    try:
        url = f"https://newsapi.org/v2/everything?q=mercado+financeiro+bitcoin+forex&language=pt&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        noticias = []
        for article in data.get("articles", [])[:3]:
            titulo = article.get("title", "").split(" - ")[0]
            noticias.append(f"📰 {titulo}")
        return "\n".join(noticias) if noticias else "📰 Sem notícias disponíveis no momento."
    except:
        return "📰 Não foi possível carregar as notícias hoje."

def buscar_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
        response = requests.get(url)
        data = response.json()
        btc = data["bitcoin"]
        eth = data["ethereum"]
        btc_change = btc["usd_24h_change"]
        eth_change = eth["usd_24h_change"]
        btc_emoji = "🟢" if btc_change > 0 else "🔴"
        eth_emoji = "🟢" if eth_change > 0 else "🔴"
        return (
            f"{btc_emoji} BTC: US$ {btc['usd']:,.0f} ({btc_change:+.2f}%)\n"
            f"{eth_emoji} ETH: US$ {eth['usd']:,.0f} ({eth_change:+.2f}%)"
        )
    except:
        return "₿ Cotações crypto indisponíveis no momento."

def buscar_forex():
    try:
        return (
            "💵 USD/BRL — acompanhe a abertura\n"
            "🇪🇺 EUR/USD — atenção aos dados econômicos\n"
            "🇬🇧 GBP/USD — volatilidade esperada"
        )
    except:
        return "💱 Cotações forex indisponíveis no momento."

async def enviar_resumo():
    bot = Bot(token=TOKEN)
    data_hoje = datetime.now().strftime('%d/%m/%Y')
    noticias = buscar_noticias()
    crypto = buscar_crypto()
    forex = buscar_forex()
    mensagem = f"""
📢 *Bom dia, traders!*
Aqui está o resumo do mercado para hoje, *{data_hoje}*
━━━━━━━━━━━━━━━━━
📰 *Notícias do Dia*
{noticias}
━━━━━━━━━━━━━━━━━
₿ *Crypto — Agora*
{crypto}
━━━━━━━━━━━━━━━━━
💱 *Forex — Atenção*
{forex}
━━━━━━━━━━━━━━━━━
⚠️ *Gestão de Risco*
➡️ Opere com no máximo 2% da banca por entrada
➡️ Respeite suporte e resistência
➡️ Dia volátil? Reduza o lote e preserve o seu capital
_Boas operações! Disciplina acima de tudo._ 🎯
"""
    await bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
    print(f"✅ Mensagem enviada: {datetime.now()}")

async def main():
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(enviar_resumo, 'cron', hour=9, minute=0)
    scheduler.start()
    print("🤖 Bot rodando... envio diário às 9h Brasília")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
