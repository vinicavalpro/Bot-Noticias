import asyncio
import os
import requests
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, date

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")


def buscar_noticias():
    """Busca as top headlines financeiras do dia em PT e EN."""
    noticias = []
    hoje = date.today().strftime("%Y-%m-%d")

    # 1. Tenta top-headlines Brasil (tempo real)
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?category=business&country=br"
            f"&pageSize=5&apiKey={NEWS_API_KEY}"
        )
        data = requests.get(url, timeout=10).json()
        for a in data.get("articles", [])[:5]:
            titulo = a.get("title", "").split(" - ")[0].strip()
            if titulo and len(titulo) > 15:
                noticias.append(f"\U0001f4f0 {titulo}")
    except Exception:
        pass

    # 2. Se trouxer menos de 3, complementa com busca EN financeira do dia
    if len(noticias) < 3:
        try:
            url = (
                f"https://newsapi.org/v2/everything"
                f"?q=bitcoin+OR+forex+OR+ibovespa+OR+%22interest+rates%22+OR+%22stock+market%22"
                f"&language=en&sortBy=publishedAt&from={hoje}"
                f"&pageSize=5&apiKey={NEWS_API_KEY}"
            )
            data = requests.get(url, timeout=10).json()
            for a in data.get("articles", [])[:5]:
                titulo = a.get("title", "").split(" - ")[0].strip()
                fonte = a.get("source", {}).get("name", "")
                if titulo and len(titulo) > 15 and len(noticias) < 5:
                    noticias.append(f"\U0001f4f0 {titulo} ({fonte})")
        except Exception:
            pass

    if noticias:
        return "\n".join(noticias[:5])
    return "\U0001f4f0 Sem notícias disponíveis no momento. Verifique os mercados manualmente."


def buscar_crypto():
    try:
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum,solana"
            "&vs_currencies=usd&include_24hr_change=true"
        )
        data = requests.get(url, timeout=10).json()
        linhas = []
        ativos = [
            ("bitcoin", "BTC"),
            ("ethereum", "ETH"),
            ("solana", "SOL"),
        ]
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
        if brl:
            linhas.append(f"\U0001f4b5 USD/BRL: R$ {brl:.2f}")
        if eur:
            linhas.append(f"\U0001f1ea\U0001f1fa EUR/USD: {1/eur:.4f}")
        if gbp:
            linhas.append(f"\U0001f1ec\U0001f1e7 GBP/USD: {1/gbp:.4f}")
        return "\n".join(linhas) if linhas else "\U0001f4b1 Cotações forex indisponíveis."
    except Exception:
        return "\U0001f4b1 Cotações forex indisponíveis no momento."


async def enviar_resumo():
    bot = Bot(token=TOKEN)
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    dia_semana = [
        "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"
    ][datetime.now().weekday()]

    noticias = buscar_noticias()
    crypto = buscar_crypto()
    forex = buscar_forex()

    mensagem = f"""
\U0001f4e2 *Bom dia, traders!*
{dia_semana}, *{data_hoje}* — Resumo do mercado
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
\U0001f4f0 *Notícias do Dia*
{noticias}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
\u20bf *Crypto — Agora*
{crypto}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
\U0001f4b1 *Forex — Cotações*
{forex}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
\u26a0\ufe0f *Gestão de Risco*
\u27a1\ufe0f Opere com no máximo 2% da banca por entrada
\u27a1\ufe0f Respeite suporte e resistência
\u27a1\ufe0f Dia volátil? Reduza o lote e preserve o seu capital
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
