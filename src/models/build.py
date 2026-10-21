"""Creates the segmentation model from a config."""
import segmentation_models_pytorch as smp


def build_model(cfg):
    cls = getattr(smp, cfg["model"])  # e.g. Unet
    return cls(encoder_name=cfg["encoder"], encoder_weights="imagenet",
               in_channels=3, classes=cfg["num_classes"])
