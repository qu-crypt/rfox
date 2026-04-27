"""List connected dongles."""
HELP = "List attached RfCat-compatible dongles"


def add_args(p):
    pass


def prompt(args):
    pass


def run(args):
    from .. import dongle
    devs = dongle.list_dongles()
    if not devs:
        print("no rfcat dongles found.")
        return 1
    print(f"{'idx':<4} {'vid:pid':<10} {'devnum':<8}")
    for idx, vid, pid, devnum in devs:
        print(f"{idx:<4} {vid:#06x}:{pid:#06x}  {devnum}")
    return 0
