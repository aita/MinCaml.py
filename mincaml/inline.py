from pyrsistent import pmap

from . import logger
from . import alpha


def size(e):
    if e[0] in ("IfEq", "IfLE"):
        e1, e2 = e[3], e[4]
    elif e[0] == "Let":
        e1, e2 = e[1], e[2]
    elif e[0] == "LetRec":
        e1, e2 = e[1].body, e[2]
    elif e[0] == "LetTuple":
        return 1 + size(e[3])
    else:
        return 1

    return 1 + size(e1) + size(e2)


class Visitor:
    def __init__(self, threshold):
        self.threshold = threshold

    def visit(self, env, e):
        method = "visit_" + e[0]
        if hasattr(self, method):
            visitor = getattr(self, method)
            return visitor(env, e)
        else:
            return e

    def visit_IfEq(self, env, e):
        return (e[0], e[1], e[2], self.visit(env, e[3]), self.visit(env, e[4]))

    def visit_IfLE(self, env, e):
        return (e[0], e[1], e[2], self.visit(env, e[3]), self.visit(env, e[4]))

    def visit_Let(self, env, e):
        return (e[0], e[1], self.visit(env, e[2]), self.visit(env, e[3]))

    def visit_LetRec(self, env, e):
        fundef = e[1]
        if size(fundef.body) <= self.threshold:
            env = env.set(fundef.name, (fundef.args, fundef.body))
        return (
            e[0],
            fundef._replace(body=self.visit(env, fundef.body)),
            self.visit(env, e[2]),
        )

    def visit_App(self, env, e):
        x, ys = e[1], e[2]
        if x not in env:
            return e

        zs, e = env[x]
        logger.info(f"inlining {x}.")
        new_env = {}
        for (z, t), y in zip(zs, ys):
            new_env[z] = y
        return alpha.conversion(e, pmap(new_env))

    def visit_LetTuple(self, env, e):
        return (e[0], e[1], e[2], self.visit(env, e[3]))


def expand(threshold, e):
    return Visitor(threshold).visit(pmap(), e)
