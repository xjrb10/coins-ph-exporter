import os
from http import HTTPStatus
from typing import *
from time import time

import requests
from flask import Flask, abort
from prometheus_client import Summary, make_wsgi_app, Gauge
import math

API_BASE_URL = "https://quote.coins.ph/v2/markets"

app = Flask(__name__)

bid_metrics = {}  # type: Dict[str, Gauge]
ask_metrics = {}  # type: Dict[str, Gauge]

request_duration = Summary("request_duration_seconds", "Time spent in the scrape_symbol() function")

cache = {}  # type: Dict[str, Dict[str, Union[str, float]]]
cache_expiry = 0


def scrape_symbols(symbols: List[str]) -> Dict[str, Tuple[float, float]]:
    """
    this supports per-symbol caching (for future edge-cases that may have variable rate expiry times)
    only sends a request to coins.ph API once for the entire list, independent of symbol cache

    Returns a list of tuple of bid and ask respectively
    """
    global cache, cache_expiry

    data = requests.get(API_BASE_URL).json()

    def scrape_symbol(symbol: str):
        if symbol in cache and cache[symbol]["expiry"] > time():
            return cache[symbol]["bid"], cache[symbol]["ask"]

        for i in data.get("markets"):
            if i.get("symbol") == symbol:
                cache[symbol] = dict([(j, float(i.get(j))) for j in ("bid", "ask")])
                cache[symbol]["expiry"] = time() + i.get("expires_in_seconds")
                return cache[symbol]["bid"], cache[symbol]["ask"]
        return math.inf, math.inf

    return dict([(symbol, scrape_symbol(symbol)) for symbol in symbols])


@request_duration.time()
@app.route("/<symbols>/metrics")
def symbol_metrics(symbols: str):
    """
    Supports multiple comma delimited symbol pairs

    e.g. /BTC-PHP,ETH-PHP/metrics

    :param symbols:
    :return:
    """
    for symbol, results in scrape_symbols(symbols.split(",")).items():
        if any([math.isinf(i) for i in results]):
            return abort(HTTPStatus.NOT_FOUND)

        global bid_metrics, ask_metrics
        if symbol not in bid_metrics:
            metric_prefix = symbol.lower().replace("-", "_")
            arrows = symbol.split("-")
            bid_metrics[symbol] = Gauge(f"{metric_prefix}_bid_price", f"Price when converting {'->'.join(arrows)}")
            ask_metrics[symbol] = Gauge(f"{metric_prefix}_ask_price", f"Price when converting {'->'.join(reversed(arrows))}")

        bid_metrics[symbol].set(results[0])
        ask_metrics[symbol].set(results[1])

    return make_wsgi_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.getenv("HTTP_SERVER_PORT", 9696))
