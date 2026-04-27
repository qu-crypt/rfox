"""Shared argparse helpers used by every command module."""
from ..config import RFConfig, MOD_NAMES, SYNC_MODES


def add_radio_args(p, *, freq=True, drate=True, mod=True, bw=True,
                   sync=False, deviation=False, channel=False,
                   pktlen=False, power=False, preamble=False, fixed=False):
    """Attach a consistent set of -f/-r/-m/-bw flags to a parser."""
    if freq:
        p.add_argument("-f", "--freq", type=float, default=None,
                       help="frequency in Hz (default: 433.92e6)")
    if drate:
        p.add_argument("-r", "--drate", type=float, default=None,
                       help="modem data rate in bps (default: 4800)")
    if mod:
        p.add_argument("-m", "--modulation", choices=MOD_NAMES, default=None,
                       help="modulation (default: OOK)")
    if bw:
        p.add_argument("--chanbw", type=float, default=None,
                       help="channel bandwidth in Hz (default: 60000)")
    if deviation:
        p.add_argument("--deviation", type=float, default=None,
                       help="FSK deviation in Hz (default: 20000)")
    if sync:
        p.add_argument("--sync-mode", choices=SYNC_MODES, default=None,
                       help="sync mode (default: NONE)")
        p.add_argument("--sync-word", type=lambda x: int(x, 0), default=None,
                       help="16-bit sync word, e.g. 0xd391")
    if channel:
        p.add_argument("--channel", type=int, default=None)
    if pktlen:
        p.add_argument("--pktlen", type=int, default=None,
                       help="packet length (default: 250)")
    if fixed:
        p.add_argument("--variable-length", action="store_true",
                       help="use variable-length packets instead of fixed")
    if power:
        p.add_argument("--power", type=lambda x: int(x, 0), default=None,
                       help="0..255 (default: 0xc0)")
    if preamble:
        p.add_argument("--preamble", type=int, default=None,
                       help="preamble bytes (default: 4)")


def add_dongle_args(p):
    p.add_argument("-i", "--index", type=int, default=0,
                   help="dongle index (default: 0)")
    p.add_argument("--debug", action="store_true",
                   help="enable libusb debug output")


def cfg_from_args(args, base: RFConfig = None) -> RFConfig:
    """Merge CLI args (potentially with --preset / --profile) onto a base."""
    cfg = base or RFConfig()
    # --preset and --profile override the base
    if getattr(args, "preset", None):
        from .. import presets
        cfg = presets.get(args.preset)
    if getattr(args, "profile", None):
        from .. import profiles
        cfg = profiles.load(args.profile)

    for field, attr in [
        ("freq", "freq"),
        ("drate", "drate"),
        ("modulation", "modulation"),
        ("chanbw", "chanbw"),
        ("deviation", "deviation"),
        ("sync_mode", "sync_mode"),
        ("sync_word", "sync_word"),
        ("channel", "channel"),
        ("pktlen", "pktlen"),
        ("power", "power"),
        ("preamble", "preamble"),
    ]:
        v = getattr(args, attr, None)
        if v is not None:
            setattr(cfg, field, v)

    if getattr(args, "variable_length", False):
        cfg.fixed_len = False

    return cfg


def add_profile_preset(p):
    p.add_argument("--preset", help="start from a built-in preset")
    p.add_argument("--profile", help="start from a saved profile")


def hex_arg(s):
    """Parse --hex 'aa bb cc' or 'aabbcc' as bytes."""
    s = s.replace(" ", "").replace(":", "")
    if s.startswith("0x") or s.startswith("0X"):
        s = s[2:]
    return bytes.fromhex(s)


def bin_arg(s):
    """Parse a binary string like '1100101' as int + bit length."""
    s = s.strip()
    if not all(c in "01" for c in s):
        raise ValueError(f"not a binary string: {s!r}")
    return int(s, 2), len(s)
