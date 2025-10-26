import logging
from pathlib import Path
from typing import List

import onnxruntime as ort
import torch
from optimum.onnxruntime import ORTModelForSequenceClassification
from transformers import AutoTokenizer

from goquant.sentiment_analysis.base import BaseSentimentAnalyzer

logger = logging.getLogger(__name__)


class OnnxFinBert(BaseSentimentAnalyzer):
    def __init__(
        self,
        model_path: Path = Path("models/finbert_onnx_quantized_dynamic"),
        file_name="model_quantized.onnx",
        batch_size: int = 32,
    ):
        logger.info("Loading ONNX FinBERT model from %s", model_path)
        try:
            session_options = ort.SessionOptions()
            session_options.graph_optimization_level = (
                ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            )
            session_options.intra_op_num_threads = 4
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

            self.model = ORTModelForSequenceClassification.from_pretrained(
                model_path,
                file_name=file_name,
                local_files_only=True,
                session_options=session_options,  # TODO: Verify if this is actually useful
                provider="CPUExecutionProvider",
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path, local_files_only=True
            )

            self.batch_size = batch_size
            logger.info("ONNX FinBERT model loaded successfully.")
        except Exception as e:
            logger.error("Error loading ONNX FinBERT model: %s", e)
            raise

    def tokenize(self, texts: str | list[str] | list[list[str]]):
        """Tokenize input texts."""
        return self.tokenizer(texts, return_tensors="pt", truncation=True, padding=True)

    def predict(self, texts: str | list[str] | list[list[str]]) -> List:
        """Predict sentiment for input texts using batch inference."""
        all_results = []
        if not texts:
            return all_results

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]

            valid_batch = [t for t in batch if isinstance(t, str) and t.strip()]
            if not valid_batch:
                continue

            # Tokenize
            try:
                inputs = self.tokenize(batch)
            except Exception as e:
                logger.warning("Error tokenizing batch: %s", e)
                continue

            # Inference
            try:
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    probs = torch.softmax(outputs.logits, dim=-1)  #
                all_results.extend(probs.cpu().numpy())
            except Exception as e:
                logger.error("Error during model inference: %s", e)
                continue

        return all_results


# if __name__ == "__main__":
#
#     texts = ["Stocks rallied and the British pound gained."]
#     finbert_onnx = OnnxFinBert()
#     # times = 0
#     # for i in range(10):
#     #     start = time.time()
#     #     probs = finbert_onnx.predict(texts)
#     #     end = time.time()
#     #     times = times + (end - start)
#     # print(f"Average time taken: {times / 10} seconds")
#     print("hello")
#     probs = finbert_onnx.predict(texts)
#     print(probs)
