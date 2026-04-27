"""Receive frames and print them. Equivalent to AMOOKScanner."""
import sys
import time
from . import _common

HELP = "RX loop: print every received frame as hex (with optional pcap log)"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, fixed=True)
    p.add_argument("-n", "--count", type=int, default=0,
                   help="stop after N frames (default: forever)")
    p.add_argument("-o", "--output", help="also write frames to a pcap file")
    p.add_argument("--timeout-ms", type=int, default=1000)
    p.add_argument("--min-rssi", type=float, default=None,
                   help="drop frames below this RSSI dBm")


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.drate = float(input(f"drate bps [{args.drate or 4800}]: ") or (args.drate or 4800))
    args.modulation = input(f"modulation [{args.modulation or 'OOK'}]: ").strip() or (args.modulation or "OOK")
    n = input(f"count [{args.count or 'forever'}]: ").strip()
    if n:
        args.count = int(n)
    o = input("output pcap [none]: ").strip()
    if o:
        args.output = o


def run(args):
    from .. import dongle, pcap
    cfg = _common.cfg_from_args(args)
    print(f"# scanning: {cfg.summary()}")

    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)
    d.setModeRX()

    writer_ctx = pcap.PcapWriter(args.output) if args.output else None
    writer = writer_ctx.__enter__() if writer_ctx else None

    seen = 0
    try:
        while True:
            try:
                payload, ts = d.RFrecv(args.timeout_ms)
            except Exception as e:
                # ChipconUsbTimeoutException etc. — keep going
                if "Timeout" in repr(e):
                    continue
                raise
            try:
                rssi = d.getRSSI()
                rssi = -float(rssi[0]) if isinstance(rssi, (bytes, bytearray)) else float(rssi)
            except Exception:
                rssi = 0.0
            if args.min_rssi is not None and rssi < args.min_rssi:
                continue

            print(f"[{ts:.3f}] rssi={rssi:6.1f} dBm  ({len(payload)} bytes) {payload.hex()}")
            if writer:
                writer.write(pcap.CapturedFrame(ts=time.time(), cfg=cfg,
                                                rssi=rssi, payload=payload))
            seen += 1
            if args.count and seen >= args.count:
                break
    except KeyboardInterrupt:
        print("\n# stopped by user.")
    finally:
        if writer_ctx:
            writer_ctx.__exit__(None, None, None)
        try:
            d.setModeIDLE()
        except Exception:
            pass

    print(f"# {seen} frames captured.")
    return 0
