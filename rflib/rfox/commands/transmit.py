"""Transmit PWM-encoded OOK from a binary string. Equivalent to AMOOKTransmit."""
from . import _common

HELP = "Transmit a binary key as OOK (PWM-encoded by default)"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, power=True, fixed=True)
    g = p.add_mutually_exclusive_group(required=False)
    g.add_argument("-b", "--bits", help="raw binary string (sent as-is)")
    g.add_argument("-c", "--compact", help="compact binary, "
                   "expanded with 0->1110, 1->1100 (PWM)")
    p.add_argument("-t", "--repeat", type=int, default=15,
                   help="repeat count (default: 15)")


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.drate = float(input(f"drate bps [{args.drate or 4800}]: ") or (args.drate or 4800))
    mode = input("input mode [bits/compact]: ").strip().lower() or "compact"
    val = input(f"{mode} string: ").strip()
    if mode == "bits":
        args.bits = val
    else:
        args.compact = val
    n = input(f"repeat [{args.repeat}]: ").strip()
    if n:
        args.repeat = int(n)


def _pwm_expand(compact):
    out = []
    for c in compact:
        if c == "0":
            out.append("1110")
        elif c == "1":
            out.append("1100")
        elif c.lower() == "x":
            out.append("0000")
        else:
            raise ValueError(f"bad compact char: {c!r}")
    return "".join(out)


def _bits_to_bytes(bits):
    # right-pad to byte boundary
    pad = (8 - len(bits) % 8) % 8
    bits = bits + "0" * pad
    return bytes(int(bits[i:i+8], 2) for i in range(0, len(bits), 8))


def run(args):
    from .. import dongle
    if not args.bits and not args.compact:
        print("provide --bits or --compact (run again with -h)")
        return 2
    bits = args.bits if args.bits else _pwm_expand(args.compact)
    payload = _bits_to_bytes(bits)

    cfg = _common.cfg_from_args(args)
    print(f"# tx {len(payload)}B x{args.repeat} on {cfg.summary()}")

    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)
    for _ in range(args.repeat):
        d.RFxmit(payload)
    d.setModeIDLE()
    return 0
