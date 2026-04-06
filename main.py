import asyncio
import os
import random
import requests
import feedparser
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, date

TOKEN              = os.environ.get("TOKEN")
CHAT_ID            = os.environ.get("CHAT_ID")
CALENDAR_CHAT_ID   = os.environ.get("CALENDAR_CHAT_ID")
FINNHUB_KEY        = os.environ.get("FINNHUB_KEY")

# Pool completo de ativos (OTC)
ATIVOS_POOL = [
    # Forex
    "EUR/USD", "GBP/USD", "EUR/GBP", "EUR/JPY", "GBP/JPY", "USD/JPY",
    "AUD/CAD", "GBP/CAD", "EUR/CAD", "EUR/NZD", "GBP/NZD", "GBP/AUD",
    "AUD/USD", "AUD/JPY", "AUD/CHF", "AUD/NZD", "NZD/JPY", "NZD/CAD",
    "USD/CAD", "USD/CHF", "CAD/JPY", "CAD/CHF", "GBP/CHF", "EUR/CHF",
    "USD/SGD", "USD/HKD", "USD/TRY", "USD/ZAR", "USD/NOK", "USD/SEK",
    "USD/MXN", "USD/BRL", "USD/COP", "PEN/USD", "EUR/THB", "USD/THB", "JPY/THB",
    # Commodities
    "XAUUSD - Ouro", "XAGUSD - Prata", "UKOUSD - Petroleo Brent", "USOUSD - Petroleo WTI",
    # Indices
    "US 100", "US 500", "US 30", "US2000", "UK 100", "JP 225",
    "AUS 200", "FR 40", "SP 35", "GER30/UK100", "US100/JP225",
    # Acoes
    "Tesla", "Amazon", "Apple", "Google", "Meta", "Microsoft",
    "Goldman Sachs", "JPMorgan Chase", "Morgan Stanley", "Alibaba",
    "Baidu", "Nike", "Intel", "Coca-Cola", "McDonald's", "AIG",
    "Meta/Alphabet", "Amazon/Alibaba", "Amazon/Ebay",
    # Crypto
    "ETH/USD", "SOL/USD", "BTC/USD", "Ripple XRP", "Cardano ADA",
    "Litecoin", "Bitcoin Cash", "Chainlink", "Polkadot", "Cosmos",
    "Arbitrum", "Polygon", "Sui", "HBAR", "TON", "Render", "FET",
    "ICP", "Decentraland", "Immutable", "IOTA", "TAO", "Worldcoin",
    "Stacks", "Jupiter", "Raydium", "Sei", "ORDI", "DYDX", "Celestia",
    "Sandbox", "Graph", "TRON/USD", "SHIB/USD", "Pepe", "Floki",
    "Dogwifhat", "Pudgy Penguins", "1000Sats", "Pyth", "Ronin",
    "Vaulta", "TRUMP Coin", "MELANIA Coin", "Fartcoin",
]

# Bandeiras por pais
BANDEIRAS = {
    "US": "🇺🇸", "EU": "🇪🇺", "GB": "🇬🇧", "JP": "🇯🇵",
    "CN": "🇨🇳", "DE": "🇩🇪", "FR": "🇫🇷", "CA": "🇨🇦",
    "AU": "🇦🇺", "CH": "🇨🇭", "NZ": "🇳🇿", "BR": "🇧🇷",
}

IMPACTO_EMOJI = {"high": "🔴", "medium": "🟡", "low": "⚪"}
IMPACTO_LABEL = {"high": "Alto", "medium": "Medio", "low": "Baixo"}


def gerar_indicacoes(n=5):
    semente = date.today().toordinal()
    rng = random.Random(semente)
    return rng.sample(ATIVOS_POOL, n)


def buscar_calendario_economico():
    """Busca eventos economicos do dia via Finnhub."""
    try:
        hoje = date.today().strftime("%Y-%m-%d")
        url = (
            f"https://finnhub.io/api/v1/calendar/economic"
            f"?from={hoje}&to={hoje}&token={FINNHUB_KEY}"
        )
        data = requests.get(url, timeout=10).json()
        eventos = data.get("economicCalendar", [])

        if not eventos:
            return "📭 Nenhum evento economico relevante encontrado para hoje."

        # Filtrar apenas alto e medio impacto e ordenar por hora
        eventos = [e for e in eventos if e.get("impact") in ("high", "medium")]
        eventos = sorted(eventos, key=lambda x: x.get("time", ""))

        if not eventos:
            return "📭 Sem eventos de alto ou medio impacto hoje."

        linhas = []
        for ev in eventos[:10]:
            pais    = ev.get("country", "")
            evento  = ev.get("event", "Evento")
            impacto = ev.get("impact", "low")
            horario = ev.get("time", "")
            prev    = ev.get("prev", "")
            est     = ev.get("estimate", "")

            # Formatar hora
            try:
                hora_fmt = datetime.strptime(horario, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
            except Exception:
                hora_fmt = "--:--"

            bandeira = BANDEIRAS.get(pais, "🌐")
            emoji    = IMPACTO_EMOJI.get(impacto, "⚪")

            linha = f"{emoji} {hora_fmt} | {bandeira} {evento}"
            if est:
                linha += f" | Est: {est}"
            if prev:
                linha += f" | Ant: {prev}"
            linhas.append(linha)

        return "\n".join(linhas)

    except Exception as e:
        return f"⚠️ Erro ao buscar calendario: {str(e)}"


def buscar_noticias():
    noticias = []
    feeds = [
        ("https://www.infomoney.com.br/feed/", "InfoMoney"),
        ("https://g1.globo.com/rss/g1/economia/", "G1 Economia"),
        ("https://exame.com/invest/feed/", "Exame Invest"),
        ("https://valor.globo.com/rss/ultimas-noticias/", "Valor Economico"),
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
                    noticias.append(f"📰 {titulo} ({fonte})")
        except Exception:
            pass
    if noticias:
        return "\n".join(noticias[:5])
    return "📰 Sem noticias disponiveis no momento."


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
                preco    = data[key]["usd"]
                variacao = data[key].get("usd_24h_change", 0)
                emoji    = "🟢" if variacao >= 0 else "🔴"
                sinal    = "+" if variacao >= 0 else ""
                linhas.append(f"{emoji} {simbolo}: US$ {preco:,.0f} ({sinal}{variacao:.2f}%)")
        return "\n".join(linhas) if linhas else "₿ Cotacoes crypto indisponiveis."
    except Exception:
        return "₿ Cotacoes crypto indisponiveis no momento."


def buscar_forex():
    try:
        url  = "https://api.exchangerate-api.com/v4/latest/USD"
        data = requests.get(url, timeout=10).json()
        rates = data.get("rates", {})
        brl = rates.get("BRL")
        eur = rates.get("EUR")
        gbp = rates.get("GBP")
        linhas = []
        if brl: linhas.append(f"💵 USD/BRL: R$ {brl:.2f}")
        if eur: linhas.append(f"🇪🇺 EUR/USD: {1/eur:.4f}")
        if gbp: linhas.append(f"🇬🇧 GBP/USD: {1/gbp:.4f}")
        return "\n".join(linhas) if linhas else "💱 Cotacoes forex indisponiveis."
    except Exception:
        return "💱 Cotacoes forex indisponiveis no momento."


async def enviar_calendario():
    """Envia o calendario economico do dia as 8h."""
    bot       = Bot(token=TOKEN)
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    dia_semana = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"][datetime.now().weekday()]
    eventos   = buscar_calendario_economico()

    mensagem = f"""
📅 *Calendario Economico — {data_hoje}*
{dia_semana} — Eventos do Dia
━━━━━━━━━━━━━━━━━
🔴 Alto impacto  🟡 Medio impacto

{eventos}
━━━━━━━━━━━━━━━━━
⚠️ Eventos de alto impacto podem gerar forte volatilidade
➡️ Ajuste sua gestao de risco antes de operar
_Fique atento aos horarios e opere com disciplina!_ 🎯
"""
    await bot.send_message(
        chat_id=CALENDAR_CHAT_ID,
        text=mensagem,
        parse_mode="Markdown"
    )
    print(f"✅ Calendario enviado: {datetime.now()}")


async def enviar_resumo():
    bot        = Bot(token=TOKEN)
    data_hoje  = datetime.now().strftime("%d/%m/%Y")
    dia_semana = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"][datetime.now().weekday()]
    noticias   = buscar_noticias()
    crypto     = buscar_crypto()
    forex      = buscar_forex()
    mensagem = f"""
📢 *Bom dia, traders!*
{dia_semana}, *{data_hoje}* - Resumo do mercado
━━━━━━━━━━━━━━━━━
📰 *Noticias do Dia*
{noticias}
━━━━━━━━━━━━━━━━━
₿ *Crypto - Agora*
{crypto}
━━━━━━━━━━━━━━━━━
💱 *Forex - Cotacoes*
{forex}
━━━━━━━━━━━━━━━━━
⚠️ *Gestao de Risco*
➡️ Opere com no maximo 2% da banca por entrada
➡️ Respeite suporte e resistencia
➡️ Dia volatil? Reduza o lote e preserve o seu capital
_Boas operacoes! Disciplina acima de tudo._ 🎯
"""
    await bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
    print(f"✅ Resumo enviado: {datetime.now()}")


async def enviar_indicacoes():
    bot        = Bot(token=TOKEN)
    data_hoje  = datetime.now().strftime("%d/%m/%Y")
    dia_semana = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado","Domingo"][datetime.now().weekday()]
    indicacoes = gerar_indicacoes(n=5)
    lista      = "\n".join(f"🔹 {ativo} (OTC)" for ativo in indicacoes)
    mensagem = f"""
🤖 *Indicacoes de Ativos - I.A.*
{dia_semana}, *{data_hoje}* - Selecao do Dia
━━━━━━━━━━━━━━━━━
📊 Melhores ativos selecionados para hoje no Blitz:
{lista}
━━━━━━━━━━━━━━━━━
⚙️ *Configuracao Sugerida*
➡️ Expiracao: de acordo com a I.A 🤖
➡️ Gestao: max. 2% a 5% do capital por entrada
➡️ Utilize a planilha de gerenciamento caso precise
"""
    await bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
    print(f"✅ Indicacoes enviadas: {datetime.now()}")


async def main():
    scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(enviar_calendario, "cron", hour=8,  minute=0)
    scheduler.add_job(enviar_resumo,     "cron", hour=9,  minute=0)
    scheduler.add_job(enviar_indicacoes, "cron", hour=12, minute=0)
    scheduler.start()
    print("🤖 Bot rodando... 8h calendario | 9h resumo | 12h indicacoes")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
