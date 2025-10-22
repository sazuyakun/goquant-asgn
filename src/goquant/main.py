"""This is the main script of the entire app"""

import time

from goquant.core.engine import IngestionEngine

start_time = time.time()
ingestor = IngestionEngine()
QUERY = "Tesla"
TICKER = "NVDA"

result = ingestor.run(query=QUERY, ticker=TICKER)
# print(result)
# print("\n-----------------------\n")
print(f"Reddit:\n{result['reddit']}")
print("\n-----------------------\n")
print(f"News:\n{result['news']}")
# print("\n-----------------------\n")
# print(f"Market Data:\n{result['market']}")

end_time = time.time()
print(f"Execution time: {end_time - start_time} seconds")
