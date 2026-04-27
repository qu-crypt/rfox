"""Transmit raw bytes given as hex on the CLI."""
from . import _common

HELP = "Transmit raw bytes (hex on the CLI)"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, power=True, fixed=True)
    p.add_argument("--hex", required=False, type=_common.hex_arg,
                   help="bytes to send, hex (e.g. 'aabb cc' or 0xaabbcc)")
    p.add_argument("-t", "--repeat", type=int, default=1)


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.drate = float(input(f"drate bps [{args.drate or 4800}]: ") or (args.drate or 4800))
    args.modulation = input(f"modulation [{args.modulation or 'OOK'}]: ").strip() or (args.modulation or "OOK")
    h = input("hex bytes: ").strip()
    args.hex = _common.hex_arg(h)
    n = input(f"repeat [{args.repeat}]: ").strip()
    if n:
        args.repeat = int(n)


def run(args):
    from .. import dongle
    if not args.hex:
        print("provide --hex BYTES")
        return 2
    cfg = _common.cfg_from_args(args)
    print(f"# tx {len(args.hex)}B x{args.repeat} on {cfg.summary()}")
    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)
    for _ in range(args.repeat):
        d.RFxmit(args.hex)
    d.setModeIDLE()
    return 0
