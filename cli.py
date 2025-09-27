import typer
from core.runner import register_bot, run_bot
from modules.scrape.backend.scraper import Scraper
from modules.monitoring.backend.monitor_bot import MonitorBot
from modules.account.backend.account_bot import AccountBot

app = typer.Typer()

# register bots for CLI direct use
register_bot("scrape", Scraper())
register_bot("monitor", MonitorBot())
register_bot("account", AccountBot())

@app.command()
def run(domain: str, **kwargs):
    """Run a bot: python cli.py run scrape url=https://..."""
    result = run_bot(domain, **kwargs)
    print(result)

if __name__ == "__main__":
    app()
