# scripts/build_data.py
# Run with: python scripts/build_data.py
# Or inside devcontainer terminal


from data import DataConfig, DataDownloader, ToySampleGenerator


def main():
    # 1) Config and ensure directories
    cfg = DataConfig()
    cfg.ensure_directories()
    print(f"[INFO] Data directories ready at: {cfg.data_dir.resolve()}")

    # 2) Download + extract + load all products
    downloader = DataDownloader(cfg)
    print("[STEP] Downloading and extracting dataset ...")
    products = downloader.download_and_extract_dataset()
    print(f"[OK] Loaded products: {len(products)}")

    # 3) Generate and save toy sample
    generator = ToySampleGenerator(cfg)
    print("[STEP] Generating toy sample ...")
    toy_sample = generator.generate_and_save_sample(
        products, output_path=cfg.processed_data_dir / "toy_sample.json"
    )
    print(f"[OK] Toy sample size: {len(toy_sample)}")
    print(f"[DONE] Saved to: {cfg.processed_data_dir / 'toy_sample.json'}")


if __name__ == "__main__":
    main()
