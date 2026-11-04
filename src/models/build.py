"""Build a segmentation model from the yaml. Switch models by changing model.active."""
import segmentation_models_pytorch as smp

DECODERS = {
    "unet":          smp.Unet,
    "unetplusplus":  smp.UnetPlusPlus,
    "fpn":           smp.FPN,
    "deeplabv3plus": smp.DeepLabV3Plus,
    "manet":         smp.MAnet,
    "linknet":       smp.Linknet,
    "pspnet":        smp.PSPNet,
    "pan":           smp.PAN,
}


def build_model(cfg):
    name = cfg["model"]["active"]
    if name not in cfg["models"]:
        raise ValueError(f"Model '{name}' not in yaml 'models'. Choose from {list(cfg['models'])}")
    m = cfg["models"][name]
    dec = m["decoder"].lower()
    if dec not in DECODERS:
        raise ValueError(f"Unknown decoder '{dec}'. Choose from {list(DECODERS)}")
    return DECODERS[dec](
        encoder_name=m["encoder"],
        encoder_weights=m["encoder_weights"],
        in_channels=cfg["in_channels"],
        classes=len(cfg["classes"]),
    )
