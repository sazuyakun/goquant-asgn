"""This script collects market data for a specified stock ticker using the yfinance library."""

from typing import List

import yfinance as yf

from goquant.data_collectors.base import BaseCollector
from goquant.data_collectors.models import MarketDataPoint

# from goquant.data_collectors.models import MarketDataPoint


class MarketDataCollector(BaseCollector):
    """
    Collector for Market Data using yfinance.
    """

    def fetch_data(
        self, ticker: str, period: str = "1mo", interval: str = "1d"
    ) -> List[MarketDataPoint]:
        """
        Fetches historical market data (OHLCV) for a given ticker.

        Inputs taken:
        ticker (str): The stock ticker symbol (e.g., "AAPL", "BTC-USD").
        period (str): The period of data to download. Valid periods include:
                          "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max".
        interval (str): The data interval. Valid intervals include:
                            "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo".
        """
        stock = yf.Ticker(ticker)
        hist_df = stock.history(period=period, interval=interval)
        if hist_df.empty:
            print(
                f"Warning: No data found for ticker '{ticker}' with period '{period}' and interval '{interval}'."
            )
            return []

        hist_df.reset_index(inplace=True)
        # Dynamically findig the timestamp
        timestamp_col = next(
            (col for col in hist_df.columns if "Date" in col or "Time" in col), None
        )
        if not timestamp_col:
            raise ValueError(
                "Timestamp column could not be found in the yfinance data."
            )

        hist_df.rename(
            columns={
                timestamp_col: "timestamp",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            },
            inplace=True,
        )

        # Ensure required columns exist
        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        data_records = hist_df[required_cols].to_dict(orient="records")  # type: ignore
        return [MarketDataPoint.model_validate(record) for record in data_records]
