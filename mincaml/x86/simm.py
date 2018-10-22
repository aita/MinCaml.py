from pyrsistent import pmap

from .virtual import C, Ans, Let
from .asm import free_variables


class Visitor:
    def visit(self, env, e):
        method = "visit_" + e[0]
        if hasattr(self, method):
            visitor = getattr(self, method)
            return visitor(env, e)
        else:
            return e

    def visit_Ans(self, env, e):
        exp = e[1]
        return Ans(*self.visit(env, exp))

    def visit_Let(self, env, e):
        (x, t), exp, e = e[1:]
        if exp[0] == "Set":
            i = exp[1]
            new_e = self.visit(env.set(x, i), e)
            if x in free_variables(new_e):
                return Let((x, t), ("Set", i), new_e)
            else:
                return new_e
        else:
            return Let((x, t), self.visit(env, exp), self.visit(env, e))

    def visit_Add(self, env, e):
        x, (t, y) = e[1:]
        if t != "V":
            return e
        if y in env:
            return ("Add", x, C(env[y]))
        elif x in env:
            return ("Add", y, C(env[x]))
        else:
            return e

    def visit_Sub(self, env, e):
        x, (t, y) = e[1:]
        if t != "V":
            return e
        if y in env:
            return ("Sub", x, C(env[y]))
        else:
            return e

    def visit_Ld(self, env, e):
        x, (t, y), i = e[1:]
        if t != "V":
            return e
        if y in env:
            return ("Ld", x, C(env[y]), i)
        else:
            return e

    def visit_St(self, env, e):
        x, y, (t, z), i = e[1:]
        if t != "V":
            return e
        if z in env:
            return ("St", x, y, C(env[z]), i)
        else:
            return e

    def visit_LdDF(self, env, e):
        x, (t, y), i = e[1:]
        if t != "V":
            return e
        if y in env:
            return ("LdDF", x, C(env[y]), i)
        else:
            return e

    def visit_StDF(self, env, e):
        x, y, (t, z), i = e[1:]
        if t != "V":
            return e
        if z in env:
            return ("StDF", x, y, C(env[z]), i)
        else:
            return e

    def visit_IfEq(self, env, e):
        x, (t, y), e1, e2 = e[1:]
        if t == "V" and y in env:
            return ("IfEq", x, C(env[y]), self.visit(env, e1), self.visit(env, e2))
        elif t == "V" and x in env:
            return ("IfEq", y, C(env[x]), self.visit(env, e1), self.visit(env, e2))
        else:
            return ("IfEq", x, (t, y), self.visit(env, e1), self.visit(env, e2))

    def visit_IfLE(self, env, e):
        x, (t, y), e1, e2 = e[1:]
        if t == "V" and y in env:
            return ("IfLE", x, C(env[y]), self.visit(env, e1), self.visit(env, e2))
        elif t == "V" and x in env:
            return ("IfGE", y, C(env[x]), self.visit(env, e1), self.visit(env, e2))
        else:
            return ("IfLE", x, (t, y), self.visit(env, e1), self.visit(env, e2))

    def visit_IfGE(self, env, e):
        x, (t, y), e1, e2 = e[1:]
        if t == "V" and y in env:
            return ("IfGE", x, C(env[y]), self.visit(env, e1), self.visit(env, e2))
        elif t == "V" and x in env:
            return ("IfLE", y, C(env[x]), self.visit(env, e1), self.visit(env, e2))
        else:
            return ("IfGE", x, (t, y), self.visit(env, e1), self.visit(env, e2))

    def visit_IfFEq(self, env, e):
        x, (t, y), e1, e2 = e[1:]
        return (e[0], x, (t, y), self.visit(env, e1), self.visit(env, e2))

    def visit_IfFLE(self, env, e):
        x, (t, y), e1, e2 = e[1:]
        return (e[0], x, (t, y), self.visit(env, e1), self.visit(env, e2))


def optimize(prog):
    "命令列の即値最適化"
    data, fundefs, e = prog
    visitor = Visitor()
    return (
        data,
        [f._replace(body=visitor.visit(pmap(), f.body)) for f in fundefs],
        visitor.visit(pmap(), e),
    )
