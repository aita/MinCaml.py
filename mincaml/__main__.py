import sys
import logging
import pprint
import functools

from . import logger
from . import id
from .parser import parser
from . import typing
from . import knorm
from . import alpha
from . import beta
from . import assoc
from . import inline
from . import const_fold
from . import elim


handler = logging.StreamHandler(sys.stderr)
# formatter = logging.Formatter("%(levelname)s: %(message)s")
# handler.setFormatter(formatter)
logger.addHandler(handler)


def main():
    assert len(sys.argv) == 2, "usage: mincaml FILENAME"
    fname = sys.argv[1]

    inlining_threthold = 0
    niter = 1000

    id.reset()

    with open(fname) as fp:
        input = fp.read()

    extenv = {}
    ast = parser.parse(input)
    typing.typing(ast, extenv)
    kform = alpha.conversion(knorm.normalize(ast, extenv))
    optimizer = [
        beta.reduction,
        assoc.nested_let_reduction,
        functools.partial(inline.expand, inlining_threthold),
        const_fold.constant_folding,
        elim.unused_definitions_elimination,
    ]

    for i in range(niter):
        logger.info(f"iteration {i+1}.")
        new_kform = kform
        for f in optimizer:
            new_kform = f(new_kform)
        if new_kform == kform:
            break
        kform = new_kform

    pprint.pprint(kform)


if __name__ == "__main__":
    main()
