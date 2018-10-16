from pyrsistent import pmap

from .id import gen_id
from .knorm import FunDef
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
        (x, t) = e[1]
        new_x = gen_id(x)
        return (
            e[0],
            (new_x, t),
            self.visit(env, e[2]),
            self.visit(env.set(x, new_x), e[3]),
        )

    def visit_Var(self, env, e):
        return (e[0], find(env, e[1]))

    def visit_LetRec(self, env, e):
        fundef = e[1]
        new_env1 = env.set(fundef.name, gen_id(fundef.name))
        new_env2 = new_env1.update({name: gen_id(name) for name, _ in fundef.args})
        return (
            e[0],
            FunDef(
                typ=fundef.typ,
                name=new_env1[fundef.name],
                args=[(new_env2[name], t) for name, t in fundef.args],
                body=self.visit(new_env2, fundef.body),
            ),
            self.visit(new_env1, e[2]),
        )

    def visit_App(self, env, e):
        return (e[0], find(env, e[1]), [find(env, arg) for arg in e[2]])

    def visit_Tuple(self, env, e):
        return (e[0], [find(env, name) for name in e[1]])

    def visit_LetTuple(self, env, e):
        new_env = env.update({name: gen_id(name) for name, _ in e[1]})
        return (
            e[0],
            [(new_env[name], t) for name, t in e[1]],
            find(env, e[2]),
            self.visit(new_env, e[3]),
        )

    def visit_Get(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]))

    def visit_Put(self, env, e):
        return (e[0], find(env, e[1]), find(env, e[2]), find(env, e[3]))

    def visit_ExtArray(self, env, e):
        return e

    def visit_ExtFunApp(self, env, e):
        return (e[0], e[1], [find(env, arg) for arg in e[2]])


def conversion(e):
    return Visitor().visit(pmap(), e)
