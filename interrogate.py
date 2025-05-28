from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
import sys
import os

# Initialize model and processor once
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)
model.eval()

def describe_image(image_path: str) -> str:
    """
    Generates a descriptive caption for the given image.

    Args:
        image_path (str): Path to the image.

    Returns:
        str: Caption describing the image.
    """
    image = Image.open(image_path).convert("RGB")

    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        output = model.generate(**inputs, max_new_tokens=50)

    caption = processor.batch_decode(output, skip_special_tokens=True)[0].strip()
    return caption

# CLI usage
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python interrogate.py path/to/image.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"❌ Error: File not found: {image_path}")
        sys.exit(1)

    caption = describe_image(image_path)
    print(f"\n🧠 Caption:\n{caption}\n")
