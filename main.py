import asyncio
import os
import requests
import feedparser
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, date

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def buscar_noticias():
    """Busca headlines financeiras via RSS de portais brasileiros."""
    noticias = []

    feeds = [
        ("https://www.infomoney.com.br/feed/", "InfoMoney"),
        ("https://g1.globo.com/rss/g1/economia/", "G1 Economia"),
        ("https://exame.com/invest/feed/", "Exame Invest"),
        ("https://valor.globo.com/rss/ultimas-noticias/", "Valor Econômico"),
    ]

    for url, fonte in feeds:
        if len(noticias) >= 5:
            break
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                titulo = entry.get("title", "").strip()
                titulo = titulo.split(" - ")[0].split(" | ")[0].strip()
                if titulo and len(titulo) > 15 and len(noticias) < 5:
                    noticias.append(f"\U0001f4f0 {titulo} ({fonte})")
        except Exception:
            pass

    if noticias:
        return "\n".join(noticias[:5])
    return "\U0001f4f0 Sem notícias disponíveis no momento."


def buscar_crypto():
    try:
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,solana"
            "&vs_currencies=usd&include_24hr_change=true"
        )
        data = requests.get(url, timeout=10).json()
        linhas = []
        ativos = [("bitcoin", "BTC"), ("ethereum", "ETH"), ("solana", "SOL")]
        for key, simbolo in ativos:
            if key in data:
                preco = data[key]["usd"]
                variacao = data[key].get("usd_24h_change", 0)
                emoji = "\U0001f7e2" if variacao >= 0 else "\U0001f534"
                sinal = "+" if variacao >= 0 else ""
                linhas.append(f"{emoji} {simbolo}: US$ {preco:,.0f} ({sinal}{variacao:.2f}%)")
        return "\n".join(linhas) if linhas else "\u20bf Cotações crypto indisponíveis."
    except Exception:
        return "\u20bf Cotações crypto indisponíveis no momento."


def buscar_forex():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        data = requests.get(url, timeout=10).json()
        rates = data.get("rates", {})
        brl = rates.get("BRL")
        eur = rates.get("EUR")
        gbp = rates.get("GBP")
        linhas = []
        if brl: linhas.append(f"\U0001f4b5 USD/BRL: R$ {brl:.2f}")
        if eur: linhas.append(f"\U0001f1ea\U0001f1fa EUR/USD: {1/eur:.4f}")
        if gbp: linhas.append(f"\U0001f1ec\U0001f1e7 GBP/USD: {1/gbp:.4f}")
        return "\n".join(linhas) if linhas else "\U0001f4b1 Cotações forex indisponíveis."
    except Exception:
        return "\U0001f4b1 Cotações forex indisponíveis no momento."


async def enviar_resumo():
    bot = Bot(token=TOKEN)
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    dia_semana = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][datetime.now().weekday()]
    noticias = buscar_noticias()
    crypto = buscar_crypto()
    forex = buscar_forex()
    mensagem = f"""
\U0001f4e2 *Bom dia, traders!*
{dia_semana}, *{data_hoje}* — Resumo do mercado
━━━━━━━━━━━━━━━━━
\U0001f4f0 *Notícias do Dia*
{noticias}
━━━━━━━━━━━━━━━━━
\u20bf *Crypto — Agora*
{crypto}
━━━━━━━━━━━━━━━━━
\U0001f4b1 *Forex — Cotações*
{forex}
━━━━━━━━━━━━━━━━━
⚠️ *Gestão de Risco*
➡️ Opere com no máximo 2% da banca por entrada
➡️ Respeite suporte e resistência
➡️ Dia volátil? Reduza o lote e preserve o seu capital
_Boas operações! Disciplina acima de tudo._ \U0001f3af
"""
    await bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
    print(f"\u2705 Mensagem enviada: {datetime.now()}")


async def main():
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(enviar_resumo, "cron", hour=9, minute=0)
    scheduler.start()
    print("\U0001f916 Bot rodando... envio diário às 9h Brasília")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
