"""Headless RX logger -> pcap. Same as scan but quieter / append-only."""
import time
from . import _common

HELP = "Headless RX: append every received frame to a pcap file"


def add_args(p):
    _common.add_dongle_args(p)
    _common.add_profile_preset(p)
    _common.add_radio_args(p, sync=True, deviation=True, pktlen=True,
                           preamble=True, fixed=True)
    p.add_argument("-o", "--output", required=False,
                   help="pcap file (default: rfox-YYYYmmdd-HHMMSS.pcap)")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="don't print frame summaries")
    p.add_argument("--timeout-ms", type=int, default=1000)


def prompt(args):
    args.freq = float(input(f"freq Hz [{args.freq or 433.92e6}]: ") or (args.freq or 433.92e6))
    args.drate = float(input(f"drate bps [{args.drate or 4800}]: ") or (args.drate or 4800))
    args.modulation = input(f"modulation [{args.modulation or 'OOK'}]: ").strip() or (args.modulation or "OOK")
    args.output = input(f"output pcap [{args.output or 'auto'}]: ").strip() or args.output


def run(args):
    from .. import dongle, pcap
    cfg = _common.cfg_from_args(args)

    if not args.output:
        args.output = time.strftime("rfox-%Y%m%d-%H%M%S.pcap")
    print(f"# logging to {args.output}: {cfg.summary()}")

    d = dongle.open_dongle(idx=args.index, debug=args.debug)
    dongle.apply_config(d, cfg)
    d.setModeRX()

    seen = 0
    with pcap.PcapWriter(args.output) as w:
        try:
            while True:
                try:
                    payload, ts = d.RFrecv(args.timeout_ms)
                except Exception as e:
                    if "Timeout" in repr(e):
                        continue
                    raise
                try:
                    raw = d.getRSSI()
                    raw = raw[0] if isinstance(raw, (bytes, bytearray)) else int(raw)
                    if raw >= 128:
                        raw -= 256
                    rssi = raw / 2.0 - 74.0
                except Exception:
                    rssi = 0.0
                w.write(pcap.CapturedFrame(ts=time.time(), cfg=cfg,
                                            rssi=rssi, payload=payload))
                seen += 1
                if not args.quiet:
                    print(f"[{seen:5d}] {rssi:6.1f} dBm  {len(payload):3d}B "
                          f"{payload[:24].hex()}{'...' if len(payload) > 24 else ''}")
        except KeyboardInterrupt:
            print(f"\n# stopped after {seen} frames")
        finally:
            try:
                d.setModeIDLE()
            except Exception:
                pass
    return 0
