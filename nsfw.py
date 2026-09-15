import os
from huggingface_hub import InferenceClient

MODEL = "Falconsai/nsfw_image_detection"

# Yahan apna Hugging Face token paste karo
HF_TOKEN = "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"

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is missing.")

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_TOKEN
)


def is_nsfw(image_path: str, threshold: float = 0.80) -> bool:
    try:
        result = client.image_classification(
            image_path,
            model=MODEL,
            top_k=5
        )

        for item in result:
            label = str(item.label).lower()
            score = float(item.score)

            print(f"AI: {label} = {score:.3f}")

            if label == "nsfw" and score >= threshold:
                return True

        return False

    except Exception as e:
        print("HF ERROR:", repr(e))
        return False
