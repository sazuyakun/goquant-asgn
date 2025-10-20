"""This is the main script of the entire app"""

from goquant.core.engine import IngestionEngine

ingestor = IngestionEngine()
QUERY = "Tesla"
TICKER = "NVDA"

result = ingestor.run(query=QUERY, ticker=TICKER)

print("\n-----------------------\n")
print(f"Reddit:\n{result['reddit']}")
print("\n-----------------------\n")
print(f"News:\n{result['news']}")
print("\n-----------------------\n")
print(f"Market Data:\n{result['market']}")
