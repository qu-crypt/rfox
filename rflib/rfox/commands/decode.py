"""Run rflib.bits decoders over a hex string or a pcap frame."""
from . import _common

HELP = "Decode raw bits using manchester/diff-manchester/PWM/raw"

METHODS = ("manchester", "diff-manchester", "pwm", "raw", "auto")


def add_args(p):
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--hex", type=_common.hex_arg, help="raw bytes (hex)")
    src.add_argument("--input", help="pcap to read from")
    p.add_argument("--frame-index", type=int, default=0)
    p.add_argument("-m", "--method", choices=METHODS, default="auto")
    p.add_argument("--hilo", type=int, default=1,
                   help="manchester polarity (0 or 1)")


def prompt(args):
    src = input("source [hex/pcap]: ").strip().lower() or "hex"
    if src == "hex":
        args.hex = _common.hex_arg(input("hex: ").strip())
    else:
        args.input = input("pcap path: ").strip()
    m = input(f"method {METHODS} [{args.method}]: ").strip()
    if m:
        args.method = m


def _try(name, fn, data):
    try:
        out = fn(data)
        return name, out
    except Exception as e:
        return name, f"<error: {e}>"


def _pwm_decode(data):
    """Treat each pair of bits as a PWM symbol: 10 -> 1, 01 -> 0, others -> ?."""
    bits = "".join(format(b, "08b") for b in data)
    out = []
    for i in range(0, len(bits) - 1, 2):
        pair = bits[i:i+2]
        out.append("1" if pair == "10" else "0" if pair == "01" else "?")
    return "".join(out)


def run(args):
    from .. import pcap
    from rflib import bits as rfbits

    if args.hex:
        data = args.hex
    elif args.input:
        frames = list(pcap.read(args.input))
        if not frames:
            print("empty pcap.")
            return 1
        data = frames[args.frame_index].payload
    else:
        print("provide --hex or --input")
        return 2

    methods = (args.method,) if args.method != "auto" else METHODS[:-1]
    print(f"# decode {len(data)}B  src={data.hex()[:64]}{'...' if len(data) > 32 else ''}")
    for m in methods:
        if m == "manchester":
            name, out = _try("manchester",
                             lambda d: rfbits.manchester_decode(d, hilo=args.hilo),
                             data)
        elif m == "diff-manchester":
            name, out = _try("diff-manchester",
                             rfbits.diff_manchester_decode, data)
        elif m == "pwm":
            name, out = _try("pwm", _pwm_decode, data)
        elif m == "raw":
            name = "raw"
            out = "".join(format(b, "08b") for b in data)
        else:
            continue
        if isinstance(out, bytes):
            disp = out.hex() + f" ({len(out)}B)"
        else:
            disp = str(out)
        print(f"  {name:<16} {disp}")
    return 0
