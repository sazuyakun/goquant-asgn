import concurrent.futures as cf
import time

import torch
from torch.nn.functional import softmax
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from goquant.sentiment_analysis.texts import texts

texts = [
    "bedini sg energizer (!motor)",
    "at the time of the pic it was 400hz; duty cycle: 10%",
    "tesla’s new affordable models are not new",
    "Tesla just launched two brand new, affordable models. But the catch is that they are not actually new.\r\nThe newly unveiled models are practically just a Tesla Model Y SUV and a Model 3 sedan with som… [+3634 chars]",
]

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
# tokenizer = AutoTokenizer.from_pretrained(
#     "nickmuchi/distilroberta-finetuned-financial-text-classification"
# )
# model = AutoModelForSequenceClassification.from_pretrained(
#     "nickmuchi/distilroberta-finetuned-financial-text-classification"
# )

print("Model loaded.")
start = time.time()
inputs = tokenizer(texts, return_tensors="pt", truncation=True, padding=True)

outputs = model(**inputs)

probs = softmax(outputs.logits, dim=1)

print("==================+>")
print(probs)

end = time.time()
print(f"Time taken: {end - start} seconds")
