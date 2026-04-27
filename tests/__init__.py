import os
import sys


def _setup_rfcat_paths():
    """Ensure rfcat's rflib is importable and rflib.rfox is visible.

    When running from the rfox directory Python adds the CWD to sys.path,
    causing rfox/rflib/ (no __init__.py) to be picked up as a namespace
    package before rfcat's installed rflib is found by PathFinder.

    Fix: move the rfcat editable-install finder ahead of PathFinder in
    sys.meta_path so rfcat's regular rflib package takes precedence.
    Then extend rflib.__path__ so rflib.rfox is importable.
    """
    # Move _EditableFinder before PathFinder
    editable = [f for f in sys.meta_path
                if getattr(f, '__name__', '') == '_EditableFinder']
    for finder in editable:
        sys.meta_path.remove(finder)
        pf_idx = next(
            (i for i, f in enumerate(sys.meta_path)
             if getattr(f, '__name__', '') == 'PathFinder'),
            2,
        )
        sys.meta_path.insert(pf_idx, finder)

    # Now importing rflib resolves to rfcat's package
    import rflib

    # Extend rflib's search path to include rfox's rflib/ directory
    rfox_rflib = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'rflib'))
    if rfox_rflib not in rflib.__path__:
        rflib.__path__.append(rfox_rflib)


_setup_rfcat_paths()
