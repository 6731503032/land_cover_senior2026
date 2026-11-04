"""One run of the 'how much Mae Suai data do we need' experiment."""
import time
from pathlib import Path
from torch.utils.data import DataLoader, ConcatDataset

from src.data.pairing import split_for
from src.data.seg_dataset import SegDataset
from src.training.train_one import set_seed, train_one_model


def run_fraction(fraction, cfg, device, oem_pairs, own_shuffled, oem_ids, own_ids, weights_dir):
    set_seed(cfg["train"]["seed"])
    classes = cfg["classes"]
    crop = cfg["data"]["crop_size"]
    repeat = cfg["data"]["own_repeat"]
    img_max = cfg["image_max"]
    
    model_name = cfg["model"]["active"]
    model_spec = cfg["models"][model_name]
    encoder = model_spec.get("encoder", "unknown")
    decoder = model_spec.get("decoder", "unknown")
    
    pct = int(fraction * 100)

    own_train, own_test = split_for(own_shuffled, fraction)
    k = len(own_train)

    test_loader = DataLoader(SegDataset(own_test, own_ids, classes, img_max["own"], crop, train=False),
                               batch_size=1, shuffle=False, num_workers=0)
    parts = [SegDataset(oem_pairs, oem_ids, classes, img_max["oem"], crop, train=True)]
    if k > 0:
        parts.append(SegDataset(own_train, own_ids, classes, img_max["own"], crop, train=True, repeat=repeat))
    train_dataset = ConcatDataset(parts)

    n_oem = len(oem_pairs)
    print(f"\n=== {model_name} (Encoder: {encoder} | Decoder: {decoder}) | {pct}% ===")
    print(f"Images trained on: {n_oem} OEM + {k} Mae Suai = {n_oem + k} unique images")
    print(f"Samples per epoch (Mae Suai x{repeat} repeat): {len(train_dataset)}")
    print(f"Test on {len(own_test)} {'seen' if fraction >= 1.0 else 'unseen'} Mae Suai images")

    # Measure training time
    start_time = time.time()
    
    res = train_one_model(cfg, train_dataset, test_loader, device,
                          weights_path=weights_dir / f"{model_name}_fraction_{pct}_last.pth")
    
    elapsed_seconds = time.time() - start_time
    elapsed_minutes = elapsed_seconds / 60.0
    print(f"Training completed in {elapsed_minutes:.2f} minutes ({elapsed_seconds:.1f}s)")

    # Update results with encoder, decoder, and time metrics
    res.update({
        "model": model_name,
        "encoder": encoder,
        "decoder": decoder,
        "fraction": fraction,
        "n_own_train": k,
        "n_test": len(own_test),
        "test_is_seen": bool(fraction >= 1.0),
        "train_time_sec": round(elapsed_seconds, 2),
        "train_time_min": round(elapsed_minutes, 2)
    })
    
    return res