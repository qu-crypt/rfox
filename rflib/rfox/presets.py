"""Built-in RFConfig profiles for well-known protocols."""
from .config import RFConfig


PRESETS = {
    # Generic 433 MHz garage / gate / weather-station OOK
    "ev1527": RFConfig(
        freq=433.92e6, drate=2400, modulation="OOK",
        chanbw=325_000, pktlen=4, sync_mode="NONE", sync_word=0,
    ),
    # PT2262 / SC5262 / HT600 family — same band as ev1527, slightly slower
    "pt2262": RFConfig(
        freq=433.92e6, drate=1200, modulation="OOK",
        chanbw=325_000, pktlen=3, sync_mode="NONE", sync_word=0,
    ),
    # KeeLoq rolling code (encrypted half is what's of interest, raw still useful)
    "keeloq": RFConfig(
        freq=433.92e6, drate=2000, modulation="OOK",
        chanbw=200_000, pktlen=8, sync_mode="NONE", sync_word=0,
    ),
    # 315 MHz US keyfob equivalent of the above
    "keyfob315": RFConfig(
        freq=315.0e6, drate=2400, modulation="OOK",
        chanbw=325_000, pktlen=4, sync_mode="NONE", sync_word=0,
    ),
    # 868 MHz EU short-range device band
    "srd868": RFConfig(
        freq=868.35e6, drate=4800, modulation="2FSK",
        chanbw=100_000, deviation=20_000, pktlen=64,
    ),
    # 915 MHz US ISM
    "ism915": RFConfig(
        freq=915.0e6, drate=38_400, modulation="2FSK",
        chanbw=200_000, deviation=20_000, pktlen=64,
    ),
    # TPMS sensors (varies by manufacturer, this is a common one)
    "tpms433": RFConfig(
        freq=433.92e6, drate=19_200, modulation="2FSK",
        chanbw=120_000, deviation=38_000, pktlen=10,
    ),
}


def get(name: str) -> RFConfig:
    if name not in PRESETS:
        raise KeyError(f"preset {name!r} not found. available: {sorted(PRESETS)}")
    # return a copy so the caller can mutate
    return RFConfig.from_dict(PRESETS[name].to_dict())


def names():
    return sorted(PRESETS)
