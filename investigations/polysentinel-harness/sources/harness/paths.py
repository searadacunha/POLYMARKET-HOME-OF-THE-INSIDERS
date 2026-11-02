"""Where the harness may write. A root touching a production path is refused before anything is opened."""
from pathlib import Path

HOME = Path.home()
PRODUCTION = tuple((HOME / p).resolve() for p in (
    'Projects/PolySentinel', 'Projects/PolySentinel-public', 'Projects/PolySentinel-investigation',
    '.local/state/polysentinel-signal-engine', '.local/state/polysentinel-replay', '.local/state/stop-bullshiting',
    'Documents/Stop-Bullshiting', 'Library/LaunchAgents'))


class IsolationError(RuntimeError):
    pass


def assert_isolated(root):
    root = Path(root).expanduser().resolve()
    for path in PRODUCTION:
        if root == path or path in root.parents or root in path.parents:
            raise IsolationError(f'{root} overlaps the production path {path}; the harness keeps its own state elsewhere')
    return root
