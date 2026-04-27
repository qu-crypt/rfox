"""Bit/byte-mutation fuzzer for a captured frame.

ETHICS / LEGAL: Use only against systems you own or are authorised to test.
Mutations are transmitted on-air and can disrupt or alter the behaviour of
unrelated nearby devices. See RFOX.md for the full disclaimer.
"""
import random
import time
from . import _common

HELP = "Take a captured frame, mutate bits/bytes, retransmit"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, power=True, fixed=True)
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--hex", type=_common.hex_arg, help="seed bytes (hex)")
    src.add_argument("--input", help="pcap to read seed frame from")
    p.add_argument("--frame-index", type=int, default=0,
                   help="which frame in the pcap to use as seed")
    p.add_argument("-n", "--count", type=int, default=64,
                   help="number of mutations to send")
    p.add_argument("--mode", choices=("bitflip", "byteflip", "random"),
                   default="bitflip")
    p.add_argument("--repeat", type=int, default=3,
                   help="repeat each mutation N times")
    p.add_argument("--gap-ms", type=int, default=50)
    p.add_argument("--seed", type=int, default=None)


def prompt(args):
    src = input("seed source [hex/pcap]: ").strip().lower() or "hex"
    if src == "hex":
        args.hex = _common.hex_arg(input("hex seed: ").strip())
    else:
        args.input = input("pcap path: ").strip()
    args.count = int(input(f"mutations [{args.count}]: ") or args.count)


def _mutate(seed, mode, rnd):
    out = bytearray(seed)
    if mode == "bitflip":
        i = rnd.randrange(len(out))
        b = rnd.randrange(8)
        out[i] ^= 1 << b
    elif mode == "byteflip":
        i = rnd.randrange(len(out))
        out[i] ^= rnd.randrange(256)
    else:
        i = rnd.randrange(len(out))
        out[i] = rnd.randrange(256)
    return bytes(out)


def run(args):
    from .. import dongle, pcap
    if args.hex:
        seed = args.hex
    elif args.input:
        frames = list(pcap.read(args.input))
        if not frames:
            print("empty pcap.")
            return 1
        seed = frames[args.frame_index].payload
    else:
        print("provide --hex or --input")
        return 2

    rnd = random.Random(args.seed)
    cfg = _common.cfg_from_args(args)
    print(f"# fuzz {args.count} mutations of {len(seed)}B seed (mode={args.mode})")

    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)
    try:
        for n in range(1, args.count + 1):
            payload = _mutate(seed, args.mode, rnd)
            for _ in range(args.repeat):
                d.RFxmit(payload)
                time.sleep(args.gap_ms / 1000.0)
            print(f"  [{n}/{args.count}] {payload.hex()}")
    except KeyboardInterrupt:
        print("\n# stopped by user.")
    finally:
        d.setModeIDLE()
    return 0
