import time
from pathlib import Path

import onnxruntime as ort
import torch
from optimum.onnxruntime import ORTModelForSequenceClassification
from texts import texts
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class OnnxFinBert:
    def __init__(
        self,
        model_path: Path = Path("models/finbert_onnx_quantized_dynamic"),
        file_name="model_quantized.onnx",
    ):
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
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True
        )

        self.batch_size = 32

    def tokenize(self, texts: str | list[str] | list[list[str]]):
        return self.tokenizer(texts, return_tensors="pt", truncation=True, padding=True)

    def predict(self, texts: str | list[str] | list[list[str]]):
        all_results = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]

            # Tokenize
            inputs = self.tokenize(batch)

            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1)

            all_results.extend(probs.cpu().numpy())

        return all_results


if __name__ == "__main__":
    finbert_onnx = OnnxFinBert()
    times = 0
    for i in range(10):
        start = time.time()
        probs = finbert_onnx.predict(texts)
        end = time.time()
        times = times + (end - start)
    print(f"Average time taken: {times / 10} seconds")
