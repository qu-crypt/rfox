"""Single-frequency jammer. Same idea as RFJammer.

ETHICS / LEGAL: RF jamming is illegal in most jurisdictions. Use this only
on equipment you own, in a shielded enclosure, or under written authorisation.
See RFOX.md for the full disclaimer.
"""
import time
from . import _common

HELP = "Jam a single frequency for N seconds"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, power=True, fixed=True)
    p.add_argument("-t", "--seconds", type=float, default=15.0,
                   help="jam duration in seconds (default: 15)")


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.seconds = float(input(f"duration s [{args.seconds}]: ") or args.seconds)


def run(args):
    from .. import dongle
    cfg = _common.cfg_from_args(args)
    print(f"# JAM {args.seconds:.1f}s on {cfg.summary()}")

    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)

    deadline = time.time() + args.seconds
    payload = b"\xff" * 240
    try:
        while time.time() < deadline:
            d.RFxmit(payload)
    except KeyboardInterrupt:
        print("\n# stopped by user.")
    finally:
        d.setModeIDLE()
    return 0
