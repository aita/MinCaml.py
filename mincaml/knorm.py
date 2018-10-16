from pyrsistent import pmap
from collections import namedtuple

from . import types
from . import syntax
from .id import gen_tmp_id


FunDef = namedtuple("FunDef", "typ name args body")


def factory(op, *options, flat=True):
    def _factory(*args):
        if flat:
            return (op, *options, *args)
        else:
            return (op, *options, args)

    return _factory


def insert_let(env, f, exps):
    letenv, args = [], []
    for (e, t) in exps:
        if isinstance(e, syntax.Var):
            args.append(e.name)
        else:
            x = gen_tmp_id(t)
            letenv.append(((x, t), e))
            args.append(x)

    e = f(*args)
    for (x, t1), e1 in reversed(letenv):
        e = ("Let", (x, t1), e1, e)
    return e


class Visitor:
    def __init__(self, extenv):
        self.extenv = extenv

    def visit(self, env, e):
        method = "visit_" + e.__class__.__name__
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Const(self, env, e):
        if e.typ == types.Unit:
            return ("Unit",), types.Unit
        elif e.typ == types.Bool:
            return ("Int", 1 if e.value else 0), types.Int
        elif e.typ == types.Int:
            return ("Int", e.value), types.Int
        elif e.typ == types.Float:
            return ("Float", e.value), types.Float
        else:
            raise ValueError(f"unknown constant type: {e.typ}")

    def visit_UnaryExp(self, env, e):
        if e.op == "not":
            return self.visit(
                env,
                syntax.If(
                    e, syntax.Const(types.Bool, False), syntax.Const(types.Bool, True)
                ),
            )

        if e.op == "-":
            op, typ = "Neg", types.Int
        elif e.op == "-.":
            op, typ = "FNeg", types.Float
        else:
            raise ValueError(f"unknown unary operator '{e.op}'")

        return insert_let(env, factory(op), [self.visit(env, e.arg)]), typ

    def visit_BinaryExp(self, env, e):
        if e.op in ("=", "<="):
            return self.visit(
                env,
                syntax.If(
                    e, syntax.Const(types.Bool, True), syntax.Const(types.Bool, False)
                ),
            )

        if e.op == "+":
            op, t = "Add", types.Int
        elif e.op == "-":
            op, t = "Sub", types.Int
        elif e.op == "+.":
            op, t = "FAdd", types.Float
        elif e.op == "-.":
            op, t = "FSub", types.Float
        elif e.op == "*.":
            op, t = "FMul", types.Float
        elif e.op == "/.":
            op, t = "FDiv", types.Float
        else:
            raise ValueError(f"unknown binary operator '{e.op}'")

        return (
            insert_let(
                env, factory(op), [self.visit(env, e.left), self.visit(env, e.right)]
            ),
            t,
        )

    def visit_If(self, env, e):
        if isinstance(e.cond, syntax.UnaryExp):
            if e.cond.op == "not":
                return self.visit(env, syntax.If(e.cond.arg, e.else_, e.then))

        if isinstance(e.cond, syntax.BinaryExp):
            if e.cond.op == "<=":
                op = "IfLE"
            elif e.cond.op == "=":
                op = "IfEq"
            else:
                raise ValueError(f"unknown comparison operator: {e.cond.op}")

            e3, t3 = self.visit(env, e.then)
            e4, t4 = self.visit(env, e.else_)
            return (
                insert_let(
                    env,
                    lambda x, y: (op, x, y, e3, e4),
                    [self.visit(env, e.cond.left), self.visit(env, e.cond.right)],
                ),
                t3,
            )

        return self.visit(
            env,
            syntax.If(
                syntax.BinaryExp("=", e.cond, syntax.Const(types.Bool, False)),
                e.else_,
                e.then,
            ),
        )

    def visit_Let(self, env, e):
        e1, t1 = self.visit(env, e.bound)
        e2, t2 = self.visit(env.set(e.name, e.typ), e.body)
        return ("Let", (e.name, e.typ), e1, e2), t2

    def visit_LetRec(self, env, e):
        env = env.set(e.fundef.name, e.fundef.typ)
        e2, t2 = self.visit(env, e.body)
        e1, t1 = self.visit(env.update(dict(e.fundef.args)), e.fundef.body)
        return (
            ("LetRec", FunDef(e.fundef.typ, e.fundef.name, e.fundef.args, e1), e2),
            t2,
        )

    def visit_Tuple(self, env, e):
        xs = [self.visit(env, e) for e in e.elems]
        return (
            insert_let(env, factory("Tuple", flat=False), xs),
            types.Tuple([t for _, t in xs]),
        )

    def visit_LetTuple(self, env, e):
        e1, t1 = self.visit(env, e.bound)
        e2, t2 = self.visit(env.update(dict(e.pat)), e.body)
        return insert_let(env, lambda x: ("LetTuple", e.pat, x, e2), [(e1, t1)]), t2

    def visit_Var(self, env, e):
        if e.name in env:
            return ("Var", e.name), env[e.name]
        if e.name in self.extenv:
            t = self.extenv[e.name]
            if types.is_array(t):
                return ("ExtArray", e.name), t
        raise ValueError(f"external variable {e.name} does not have an array type")

    def visit_Array(self, env, e):
        e1, t1 = self.visit(env, e.len)
        e2, t2 = self.visit(env, e.init)
        ctor = "create_float_array" if types.is_float(t2) else "create_array"
        return (
            insert_let(
                env, factory("ExtFunApp", ctor, flat=False), [(e1, t1), (e2, t2)]
            ),
            types.Array(t2),
        )

    def visit_App(self, env, e):
        if isinstance(e.fun, syntax.Var) and e.fun.name not in env:
            if e.fun.name in self.extenv and types.is_fun(self.extenv[e.fun.name]):
                return (
                    insert_let(
                        env,
                        factory("ExtFunApp", e.fun.name, flat=False),
                        [self.visit(env, arg) for arg in e.args],
                    ),
                    self.extenv[e.fun.name].ret,
                )
            else:
                raise ValueError(f"unknown external function: {e.fun.name}")

        e1, t1 = self.visit(env, e.fun)
        if types.is_fun(t1):
            return (
                insert_let(
                    env,
                    lambda x, *ys: ("App", x, ys),
                    [(e1, t1)] + [self.visit(env, arg) for arg in e.args],
                ),
                t1.ret,
            )
        else:
            raise ValueError(f"cannot apply {t1}")

    def visit_Get(self, env, e):
        e1, t1 = self.visit(env, e.array)
        if not types.is_array(t1):
            raise ValueError(f"cannot get from {t1}")
        return (
            insert_let(env, factory("Get"), [(e1, t1), self.visit(env, e.index)]),
            t1.elem,
        )

    def visit_Put(self, env, e):
        return (
            insert_let(
                env,
                factory("Put"),
                [
                    self.visit(env, e.array),
                    self.visit(env, e.index),
                    self.visit(env, e.exp),
                ],
            ),
            types.Unit,
        )


def normalize(e, extenv):
    return Visitor(extenv).visit(pmap(), e)
