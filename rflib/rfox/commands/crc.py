"""Try common CRCs against the trailing bytes of every frame in a pcap."""
from . import _common

HELP = "Try common CRCs against captured frames to identify the protocol's checksum"


CRC8_POLYS = [
    ("CRC-8 (0x07)", 0x07, 0x00, 0x00, False, False),
    ("CRC-8/MAXIM (0x31)", 0x31, 0x00, 0x00, True, True),
    ("CRC-8/CCITT (0x07)", 0x07, 0x00, 0x55, False, False),
]
CRC16_POLYS = [
    ("CRC-16/CCITT-FALSE (0x1021)", 0x1021, 0xffff, 0x0000, False, False),
    ("CRC-16/XMODEM (0x1021)", 0x1021, 0x0000, 0x0000, False, False),
    ("CRC-16/IBM (0x8005)", 0x8005, 0x0000, 0x0000, True, True),
    ("CRC-16/MODBUS (0x8005)", 0x8005, 0xffff, 0x0000, True, True),
]


def _bit_reverse(v, w):
    out = 0
    for _ in range(w):
        out = (out << 1) | (v & 1)
        v >>= 1
    return out


def _crc(data, width, poly, init, xorout, refin, refout):
    top = 1 << (width - 1)
    mask = (1 << width) - 1
    crc = init
    for b in data:
        if refin:
            b = _bit_reverse(b, 8)
        crc ^= b << (width - 8)
        for _ in range(8):
            if crc & top:
                crc = ((crc << 1) ^ poly) & mask
            else:
                crc = (crc << 1) & mask
    if refout:
        crc = _bit_reverse(crc, width)
    return crc ^ xorout


def add_args(p):
    src = p.add_mutually_exclusive_group(required=False)
    src.add_argument("--hex", type=_common.hex_arg)
    src.add_argument("--input", help="pcap path (tries every frame)")
    p.add_argument("--width", choices=("8", "16", "both"), default="both")


def prompt(args):
    src = input("source [hex/pcap]: ").strip().lower() or "hex"
    if src == "hex":
        args.hex = _common.hex_arg(input("hex: ").strip())
    else:
        args.input = input("pcap: ").strip()


def _check_one(data, polys, width):
    """Test each poly: does the trailing N bytes match crc(data[:-N])?"""
    n_bytes = width // 8
    if len(data) <= n_bytes:
        return []
    payload, tail = data[:-n_bytes], data[-n_bytes:]
    expected = int.from_bytes(tail, "big")
    expected_le = int.from_bytes(tail, "little")
    matches = []
    for name, poly, init, xorout, refin, refout in polys:
        c = _crc(payload, width, poly, init, xorout, refin, refout)
        if c == expected:
            matches.append((name, "BE"))
        elif c == expected_le:
            matches.append((name, "LE"))
    return matches


def run(args):
    from .. import pcap
    if args.hex:
        frames = [args.hex]
    elif args.input:
        frames = [f.payload for f in pcap.read(args.input)]
    else:
        print("provide --hex or --input")
        return 2

    polys8 = CRC8_POLYS if args.width in ("8", "both") else []
    polys16 = CRC16_POLYS if args.width in ("16", "both") else []

    # Per-frame match counts
    counts = {}
    for f in frames:
        for name, end in _check_one(f, polys8, 8):
            counts[(name, end)] = counts.get((name, end), 0) + 1
        for name, end in _check_one(f, polys16, 16):
            counts[(name, end)] = counts.get((name, end), 0) + 1

    if not counts:
        print(f"# no CRC match across {len(frames)} frame(s).")
        return 1

    print(f"# matches across {len(frames)} frame(s):")
    for (name, end), n in sorted(counts.items(), key=lambda kv: -kv[1]):
        marker = " <- consistent" if n == len(frames) else ""
        print(f"  {n:3d}/{len(frames)}  {name}  endian={end}{marker}")
    return 0
