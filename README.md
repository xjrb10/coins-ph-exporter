# coins-ph-exporter
Coins.ph exporter for Prometheus, intended to be ran on low-power ARMv7 Single-board Computers (SBC)s with a lightweight package footprint

### Running on docker:
```bash
docker run -d --restart unless-stopped -p 9696:9696 --name coins-ph-exporter xjrb10/coins-ph-exporter
```

### Metrics URL scheme:
I didn't want to waste several API calls to Coins.ph, each market symbol is intended to be compacted into one `metrics` call.

It intentionally uses comma sparated list items as such:
```
/BTC-PHP,ETH-PHP/metrics  # metrics for BTC-PHP and ETH-PHP, exports to the following measures:
                          #  - btc_php_bid_price
                          #  - btc_php_ask_price
                          #       - and -
                          #  - eth_php_bid_price
                          #  - eth_php_ask_price

# To only export one market "symbol", use:
/BTC-PHP/metrics  # exports as, "btc_php_bid_price" and "btc_php_ask_price"
```

Scrape it via Prometheus, make your own Grafana Dashboard, and you're set... You know the drill 😜

***An example on how to actually use it within your `prometheus.yml` file:***
```yml
scrape_configs:
  - job_name: 'coins_ph'
    scrape_interval: 1m
    metrics_path: '/BTC-PHP,ETH-PHP/metrics'
    static_configs:
      - targets: ['localhost:9696']
```
Oh yeah, to change up the port just use the `HTTP_SERVER_PORT` environment variable... Or route it via docker's networking, whichever you think is best.

# References:
 - [Coins.ph API](https://docs.coins.asia/docs/market-rates-v2)
