import sys
import logging
import pprint

from . import logger
from . import id
from .parser import parser
from . import typing
from . import knorm
from . import alpha
from . import beta
from . import assoc


handler = logging.StreamHandler(sys.stderr)
# formatter = logging.Formatter("%(levelname)s: %(message)s")
# handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    assert len(sys.argv) == 2, "usage: mincaml FILENAME"
    fname = sys.argv[1]

    with open(fname) as fp:
        input = fp.read()

    id.reset()

    extenv = {}
    e = parser.parse(input)
    typing.typing(e, extenv)
    kform, _ = knorm.normalize(e, extenv)
    pipeline = [alpha.conversion, beta.reduction, assoc.nested_let_reduction]
    for f in pipeline:
        kform = f(kform)
    pprint.pprint(kform)


if __name__ == "__main__":
    main()
