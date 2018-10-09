import sys

from . import parser
from . import typing
from . import knorm


def main():
    assert len(sys.argv) == 2, "usage: mincaml FILENAME"
    fname = sys.argv[1]

    with open(fname) as fp:
        input = fp.read()

    extenv = {}
    e = parser.parser.parse(input)
    typing.typing(e, extenv)
    ir = knorm.normalize(e, extenv)
    print(ir)


if __name__ == "__main__":
    main()
