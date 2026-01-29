#!/usr/bin/env python3
import argparse
import subprocess
import os
import toml

def train(config_path: str, dataset_path: str, output_name: str):
    """Run kohya training with config."""
    config = toml.load(config_path)

    output_dir = "/workspace/outputs"
    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "accelerate", "launch",
        "/workspace/sd-scripts/flux_train_network.py",
        f"--pretrained_model_name_or_path={config.get('model', 'black-forest-labs/FLUX.1-dev')}",
        f"--train_data_dir={dataset_path}",
        f"--output_dir={output_dir}",
        f"--output_name={output_name}",
        f"--learning_rate={config.get('learning_rate', 1e-4)}",
        f"--max_train_steps={config.get('max_steps', 1000)}",
        f"--network_dim={config.get('network_dim', 16)}",
        f"--network_alpha={config.get('network_alpha', 16)}",
        "--save_model_as=safetensors",
        "--mixed_precision=bf16",
        "--cache_latents",
    ]

    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Sync to GCS
    subprocess.run(["python3", "/workspace/scripts/sync_gcs.py", "push"])
    print(f"Training complete: {output_name}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    train(args.config, args.dataset, args.name)
