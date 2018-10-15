from pyrsistent import pmap

from . import logger
from .util import find


class BetaVisitor:
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
        letenv = e[1]
        new_env = env
        new_letenv = {}
        for name, (e1, t) in letenv.items():
            e2 = self.visit(env, e1)
            if e2[0] == "Var":
                new_name = e2[1]
                logger.info(f"beta-reduction {name} = {new_name}.")
                new_env = new_env.set(name, new_name)
            else:
                new_letenv[name] = (e2, t)
        if len(new_letenv) > 0:
            return (e[0], new_letenv, self.visit(new_env, e[2]))
        else:
            return self.visit(new_env, e[2])

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
    return BetaVisitor().visit(pmap(), e)
