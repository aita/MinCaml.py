from pyrsistent import pmap
from collections import namedtuple

from . import types
from . import syntax
from .id import gen_tmp_id


def IR(*args):
    return args


def IR_factory(op, *options):
    def _ir(*args):
        return IR(op, *options, *args)

    return _ir


FunDef = namedtuple("FunDef", "typ name args body")


class KNormalizeVisitor:
    "K正規化を行うVisitor"

    def __init__(self, extenv):
        self.extenv = extenv

    def visit(self, env, e):
        method = "visit_" + e.__class__.__name__
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Const(self, env, e):
        if e.typ == types.Unit:
            return IR("Unit"), types.Unit
        elif e.typ == types.Bool:
            return IR("Int", 1 if e.value else 0), types.Int
        elif e.typ == types.Int:
            return IR("Int", e.value), types.Int
        elif e.typ == types.Float:
            return IR("Float", e.value), types.Float
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
            raise ValueError(f"unknown operator '{e.op}'")

        return self.insert_let(env, IR_factory(op), [self.visit(env, e.arg)], typ)
        e1, t1 = self.visit(env, e.arg)
        if isinstance(e1, syntax.Var):
            return IR(op, e1.name), typ
        else:
            x = gen_tmp_id(t1)
            e2 = IR(op, x)
            return IR("Let", (x, t1), e1, e2), typ

    def visit_BinaryExp(self, env, e):
        if e.op in ("=", "<="):
            return self.visit(
                env,
                syntax.If(
                    e, syntax.Const(types.Bool, True), syntax.Const(types.Bool, False)
                ),
            )

        if e.op == "+":
            op, typ = "Add", types.Int
        elif e.op == "-":
            op, typ = "Sub", types.Int
        elif e.op == "+.":
            op, typ = "FAdd", types.Float
        elif e.op == "-.":
            op, typ = "FSub", types.Float
        elif e.op == "*.":
            op, typ = "FMul", types.Float
        elif e.op == "/.":
            op, typ = "FDiv", types.Float
        else:
            raise ValueError(f"unknown operator '{e.op}'")

        return self.insert_let(
            env,
            IR_factory(op),
            [self.visit(env, e.left), self.visit(env, e.right)],
            typ,
        )

    def visit_If(self, env, e):
        if isinstance(e.cond, syntax.UnaryExp):
            if e.cond.op == "not":
                return self.visit(env, syntax.If(e.cond.arg, e.else_, e.then))

        if isinstance(e.cond, syntax.BinaryExp):
            if e.cond.op == "<=":
                op, typ = "IfLE", types.Int
            elif e.cond.op == "=":
                op, typ = "IfEq", types.Int
            else:
                raise ValueError(f"unknown operator: {e.cond.op}")

            return self.insert_let(
                env,
                IR_factory(op),
                [self.visit(env, e.then), self.visit(env, e.else_)],
                typ,
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
        return IR("Let", {e.name: (e1, e.typ)}, e2), t2

    def visit_LetRec(self, env, e):
        env = env.set(e.fundef.name, e.fundef.typ)
        e2, t2 = self.visit(env, e.body)
        e1, t1 = self.visit(env.update(dict(e.fundef.args)), e.fundef.body)
        return (
            IR("LetRec", FunDef(e.fundef.typ, e.fundef.name, e.fundef.args, e1), e2),
            t2,
        )

    def visit_Tuple(self, env, e):
        xs = [self.visit(env, e) for e in e.elems]
        return self.insert_let(
            env, lambda *xs: IR("Tuple", xs), xs, types.Tuple([t for _, t in xs])
        )

    def visit_LetTuple(self, env, e):
        e1, t1 = self.visit(env, e.bound)
        e2, t2 = self.visit(env.update(dict(e.pat)), e.body)
        if isinstance(e1, syntax.Var):
            return IR("LetTuple", e.pat, e1, e2), t2
        else:
            x = gen_tmp_id(t1)
            e3 = IR("LetTuple", e.pat, x, e2)
            return IR("Let", {x: (e1, t1)}, e3), t2

    def visit_Var(self, env, e):
        if e.name in env:
            return IR("Var", e.name), env[e.name]
        if e.name in self.extenv:
            t = self.extenv[e.name]
            if types.is_array(t):
                return IR("ExtArray", e.name), t
        raise ValueError(f"external variable {e.name} does not have an array type")

    def visit_Array(self, env, e):
        e1, t1 = self.visit(env, e.len)
        e2, t2 = self.visit(env, e.init)
        ctor = "create_float_array" if types.is_float(t2) else "create_array"
        return self.insert_let(
            env,
            lambda *xs: IR("ExtFunApp", ctor, xs),
            [(e1, t1), (e2, t2)],
            types.Array(t2),
        )

    def visit_App(self, env, e):
        if isinstance(e.fun, syntax.Var) and e.fun.name not in env:
            if e.fun.name in self.extenv and types.is_fun(self.extenv[e.fun.name]):
                return self.insert_let(
                    env,
                    lambda *xs: IR("ExtFunApp", e.fun.name, xs),
                    [self.visit(env, arg) for arg in e.args],
                    self.extenv[e.fun.name].ret,
                )
            else:
                raise ValueError(f"unknown external function: {e.fun.name}")

        e1, t1 = self.visit(env, e.fun)
        if types.is_fun(t1):
            return self.insert_let(
                env,
                lambda x: self.insert_let(
                    env,
                    lambda *xs: IR("App", x, xs),
                    [self.visit(env, arg) for arg in e.args],
                    t1.ret,
                ),
                [(e1, t1)],
                t1.ret,
            )
        else:
            raise ValueError(f"unknown function type: {t1}")

    def visit_Get(self, env, e):
        e1, t1 = self.visit(env, e.array)
        if not types.is_array(t1):
            raise ValueError(f"cannot get from {t1}")
        return self.insert_let(
            env, IR_factory("Get"), [(e1, t1), self.visit(env, e.index)], t1.elem
        )

    def visit_Put(self, env, e):
        return self.insert_let(
            env,
            IR_factory("Put"),
            [
                self.visit(env, e.array),
                self.visit(env, e.index),
                self.visit(env, e.exp),
            ],
            types.Unit,
        )

    def insert_let(self, env, factory, exps, typ):
        letenv = {}
        args = []
        for (e, t) in exps:
            if isinstance(e, syntax.Var):
                args.append(e.name)
            else:
                x = gen_tmp_id(t)
                letenv[x] = (e, t)
                args.append(x)

        ir = factory(*args)
        if len(letenv) > 0:
            return IR("Let", letenv, ir), typ
        else:
            return ir, typ


def normalize(e, extenv):
    return KNormalizeVisitor(extenv).visit(pmap(), e)
