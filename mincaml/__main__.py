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
from . import closure
from .x86 import virtual, simm

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
    e = alpha.conversion(knorm.normalize(ast, extenv))

    optimizer = [
        beta.reduction,
        assoc.nested_let_reduction,
        functools.partial(inline.expand, inlining_threthold),
        const_fold.constant_folding,
        elim.unused_definitions_elimination,
    ]
    for i in range(niter):
        logger.info(f"iteration {i+1}.")
        new_e = e
        for f in optimizer:
            new_e = f(new_e)
        if new_e == e:
            break
        e = new_e

    pipelines = [closure.conversion, virtual.generate, simm.optimize]
    prog = e
    for f in pipelines:
        prog = f(prog)
    pprint.pprint(prog)


if __name__ == "__main__":
    main()
