#!/usr/bin/env python3
import argparse
import os
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

def caption_images(input_dir: str, model_name: str = "microsoft/Florence-2-base"):
    """Caption all images in directory using Florence-2."""
    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, trust_remote_code=True, torch_dtype=torch.float16
    ).cuda()

    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue

        img_path = os.path.join(input_dir, fname)
        caption_path = os.path.splitext(img_path)[0] + ".txt"

        if os.path.exists(caption_path):
            continue

        image = Image.open(img_path).convert("RGB")
        inputs = processor(text="<DETAILED_CAPTION>", images=image, return_tensors="pt").to("cuda")

        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=256
        )
        caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        with open(caption_path, "w") as f:
            f.write(caption)
        print(f"Captioned: {fname}")

def resize_images(input_dir: str, max_size: int = 1024):
    """Resize images to max dimension while preserving aspect ratio."""
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            continue

        img_path = os.path.join(input_dir, fname)
        img = Image.open(img_path)

        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            img.save(img_path)
            print(f"Resized: {fname}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("--type", choices=["character", "style", "concept"], default="character")
    parser.add_argument("--caption", action="store_true")
    parser.add_argument("--resize", type=int, default=1024)
    args = parser.parse_args()

    if args.resize:
        resize_images(args.input_dir, args.resize)
    if args.caption:
        caption_images(args.input_dir)

    print("Dataset preparation complete")
