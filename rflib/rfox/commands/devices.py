"""List connected dongles."""
HELP = "List attached RfCat-compatible dongles"

# CC1111 supports three sub-bands; all known dongles cover the full span.
_FREQ_RANGE = "300-928 MHz  (sub-bands: 300-348 / 389-464 / 779-928)"

_DEVICE_NAMES = {
    (0x1d50, 0x6047): "YARDStick One",
    (0x1d50, 0x6048): "RfCat CC1111EMK",
    (0x1d50, 0x605b): "DonsDongle",
    (0x1d50, 0xecc1): "rfcat (bootloader mode)",
    (0x0451, 0x4715): "TI CC1111 USB Dongle",
}


def add_args(p):
    p.add_argument("--details", "-v", action="store_true",
                   help="query firmware info from dongle (requires USB access)")


def prompt(args):
    v = input("show firmware details (requires USB access) [y/N]: ").strip().lower()
    args.details = v in ("y", "yes")


def run(args):
    from .. import dongle
    devs = dongle.list_dongles()
    if not devs:
        print("no rfcat dongles found.")
        return 1

    for idx, vid, pid, devnum in devs:
        name = _DEVICE_NAMES.get((vid, pid), "unknown rfcat device")
        print(f"[{idx}]  {name}")
        print(f"     usb    {vid:#06x}:{pid:#06x}  devnum={devnum}")
        print(f"     freq   {_FREQ_RANGE}")

        if getattr(args, "details", False):
            try:
                d = dongle.open_dongle(idx=idx)
                hw = d.reprHardwareConfig()
                sw = d.reprSoftwareConfig()
                serial = d.getDeviceSerialNumber()
                serial_str = serial.hex() if serial else "n/a"
                print(f"     serial {serial_str}")
                for line in hw.splitlines():
                    print(f"     {line.strip()}")
                for line in sw.splitlines():
                    print(f"     {line.strip()}")
            except Exception as e:
                print(f"     firmware  unavailable: {e}")
        print()

    return 0
