from pyrsistent import pmap

from . import logger
from .util import find


class Visitor:
    def visit(self, env, e):
        method = "visit_" + e[0]
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Unit(self, env, e):
        return e

    def visit_Int(self, env, e):
        return e

    def visit_Float(self, env, e):
        return e

    def visit_Neg(self, env, e):
        return (e[0], find(env, e[1]))

    def visit_Add(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_Sub(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_FNeg(self, env, e):
        return (e[0], find(env, e[1]))

    def visit_FAdd(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_FSub(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_FMul(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_FDiv(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_IfEq(self, env, e):
        return (
            e[0],
            find(env, e[1]),
            find(env, e[2]),
            self.visit(env, e[3]),
            self.visit(env, e[4]),
        )

    def visit_IfLE(self, env, e):
        return (
            e[0],
            find(env, e[1]),
            find(env, e[2]),
            self.visit(env, e[3]),
            self.visit(env, e[4]),
        )

    def visit_Let(self, env, e):
        (x, t), e1, e2 = e[1], e[2], e[3]
        new_e1 = self.visit(env, e1)
        if new_e1[0] == "Var":
            y = new_e1[1]
            logger.info(f"beta-reduction {x} = {y}.")
            return self.visit(env.set(x, y), new_e1)
        else:
            new_e2 = self.visit(env, e2)
            return (e[0], (x, t), new_e1, new_e2)

    def visit_Var(self, env, e):
        return (e[0], find(env, e[1]))

    def visit_LetRec(self, env, e):
        fundef = e[1]
        return (
            e[0],
            fundef._replace(body=self.visit(env, fundef.body)),
            self.visit(env, e[2]),
        )

    def visit_App(self, env, e):
        return (e[0], find(env, e[1]), [find(env, arg) for arg in e[2]])

    def visit_Tuple(self, env, e):
        return (e[0], [find(env, name) for name in e[1]])

    def visit_LetTuple(self, env, e):
        return (e[0], e[1], find(env, e[2]), self.visit(env, e[3]))

    def visit_Get(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_Put(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]), find(env, e[3]))

    def visit_ExtArray(self, env, e):
        return e

    def visit_ExtFunApp(self, env, e):
        return (e[0], e[1], [find(env, arg) for arg in e[2]])


def reduction(e):
    return Visitor().visit(pmap(), e)
