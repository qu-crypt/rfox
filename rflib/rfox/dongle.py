"""Helpers for opening dongles and applying an RFConfig."""
from .config import RFConfig

# Modulation name -> rflib constant. Looked up lazily so this module stays
# importable in environments without libusb.
def _mod_const(name):
    import rflib
    return {
        "OOK": rflib.MOD_ASK_OOK,
        "2FSK": rflib.MOD_2FSK,
        "GFSK": rflib.MOD_GFSK,
        "MSK": rflib.MOD_MSK,
        "4FSK": rflib.MOD_4FSK,
    }[name.upper()]


def _sync_const(name):
    import rflib
    return {
        "NONE": rflib.SYNCM_NONE,
        "15/16": rflib.SYNCM_15_of_16,
        "16/16": rflib.SYNCM_16_of_16,
        "CS": rflib.SYNCM_CARRIER,
        "CS15/16": rflib.SYNCM_CARRIER_15_of_16,
        "CS16/16": rflib.SYNCM_CARRIER_16_of_16,
        "CS30/32": rflib.SYNCM_CARRIER_30_of_32,
    }[name.upper()]


def open_dongle(idx=0, debug=False, fake=False):
    """Return an RfCat-compatible object. fake=True skips libusb."""
    if fake:
        from rflib.fakedongle_nic import FakeRfCat
        return FakeRfCat()
    import rflib
    return rflib.RfCat(idx=idx, debug=debug)


def apply_config(d, cfg: RFConfig):
    """Push every field of cfg onto the dongle."""
    d.setFreq(cfg.freq)
    d.setMdmModulation(_mod_const(cfg.modulation))
    d.setMdmDRate(cfg.drate)
    d.setMdmChanBW(cfg.chanbw)
    if cfg.modulation.upper() in ("2FSK", "GFSK", "MSK", "4FSK"):
        d.setMdmDeviatn(cfg.deviation)
    d.setChannel(cfg.channel)
    d.setMdmSyncMode(_sync_const(cfg.sync_mode))
    if cfg.sync_word:
        d.setMdmSyncWord(cfg.sync_word & 0xffff)
    d.setMdmNumPreamble(cfg.preamble)
    if cfg.fixed_len:
        d.makePktFLEN(cfg.pktlen)
    else:
        d.makePktVLEN(cfg.pktlen)
    d.setPower(cfg.power)


def list_dongles():
    """Return a list of (index, vid, pid, devnum) tuples."""
    import rflib
    out = []
    for i, dev in enumerate(rflib.getRfCatDevices()):
        out.append((i, dev.idVendor, dev.idProduct, dev.devnum))
    return out
