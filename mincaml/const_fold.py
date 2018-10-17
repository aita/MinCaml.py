from pyrsistent import pmap


def is_int(env, x):
    if x in env:
        return env[x][0] == "Int"
    return False


def is_float(env, x):
    if x in env:
        return env[x][0] == "Float"
    return False


def is_tuple(env, x):
    if x in env:
        return env[x][0] == "Tuple"
    return False


def const(env, x):
    return env[x][1]


class Visitor:
    def visit(self, env, e):
        method = "visit_" + e[0]
        if hasattr(self, method):
            visitor = getattr(self, method)
            return visitor(env, e)
        else:
            return e

    def visit_Var(self, env, e):
        x = e[1]
        if is_int(env, x):
            r = const(env, x)
            return ("Int", r)
        else:
            return e

    def visit_Neg(self, env, e):
        x = e[1]
        if is_int(env, x):
            r = -const(env, x)
            return ("Int", r)
        else:
            return e

    def visit_Add(self, env, e):
        x, y = e[1], e[1]
        if is_int(env, x) and is_int(env, y):
            r = const(env, x) + const(env, y)
            return ("Int", r)
        else:
            return e

    def visit_Sub(self, env, e):
        x, y = e[1], e[2]
        if is_int(env, x) and is_int(env, y):
            r = const(env, x) - const(env, y)
            return ("Int", r)
        else:
            return e

    def visit_FNeg(self, env, e):
        x = e[1]
        if is_float(env, x):
            r = -const(env, x)
            return ("Float", r)
        else:
            return e

    def visit_FAdd(self, env, e):
        x, y = e[1], e[2]
        if is_float(env, x) and is_float(env, y):
            r = const(env, x) + const(env, y)
            return ("Float", r)
        else:
            return e

    def visit_FSub(self, env, e):
        x, y = e[1], e[2]
        if is_float(env, x) and is_float(env, y):
            r = const(env, x) - const(env, y)
            return ("Float", r)
        else:
            return e

    def visit_FMul(self, env, e):
        x, y = e[1], e[2]
        if is_float(env, x) and is_float(env, y):
            r = const(env, x) * const(env, y)
            return ("Float", r)
        else:
            return e

    def visit_FDiv(self, env, e):
        x, y = e[1], e[2]
        if is_float(env, x) and is_float(env, y):
            r = const(env, x) / const(env, y)
            return ("Float", r)
        else:
            return e

    def visit_IfEq(self, env, e):
        x, y, e1, e2 = e[1:]
        if (is_int(env, x) and is_int(env, y)) or (
            is_float(env, x) and is_float(env, y)
        ):
            if const(env, x) == const(env, y):
                return self.visit(env, e1)
            else:
                return self.visit(env, e2)
        return (e[0], x, y, self.visit(env, e1), self.visit(env, e2))

    def visit_IfLE(self, env, e):
        x, y, e1, e2 = e[1:]
        if (is_int(env, x) and is_int(env, y)) or (
            is_float(env, x) and is_float(env, y)
        ):
            if const(env, x) <= const(env, y):
                return self.visit(env, e1)
            else:
                return self.visit(env, e2)
        return (e[0], x, y, self.visit(env, e1), self.visit(env, e2))

    def visit_Let(self, env, e):
        (x, t), e1, e2 = e[1:]
        new_e1 = self.visit(env, e1)
        new_e2 = self.visit(env.set(x, new_e1), e2)
        return (e[0], (x, t), new_e1, new_e2)

    def visit_LetRec(self, env, e):
        fundef, e2 = e[1], e[2]
        return (
            e[0],
            fundef._replace(body=self.visit(env, fundef.body)),
            self.visit(env, e2),
        )

    def visit_LetTuple(self, env, e):
        xts, y, e1 = e[1:]
        if is_tuple(env, y):
            new_e1 = self.visit(env, e1)
            for xt, z in zip(xts, env[y][1]):
                new_e1 = ("Let", xt, ("Var", z), new_e1)
            return new_e1
        else:
            return (e[0], xts, y, self.visit(env, e1))


def constant_folding(e):
    return Visitor().visit(pmap(), e)
