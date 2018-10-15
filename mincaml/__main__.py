import sys
import logging
import pprint

from . import id
from . import parser
from . import typing
from . import knorm
from . import logger


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
    e = parser.parser.parse(input)
    typing.typing(e, extenv)
    ir = knorm.normalize(e, extenv)
    pprint.pprint(ir)


if __name__ == "__main__":
    main()
