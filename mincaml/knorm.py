from pyrsistent import pmap

from . import types
from . import syntax
from .id import gen_tmp_id


class IR(list):
    "K正規系の中間表現クラス"

    def __init__(self, *args):
        super().__init__(args)


class FunDef:
    def __init__(self, typ, name, args, body):
        self.typ = typ
        self.name = name
        self.args = args
        self.body = body


class KNormalizeVisitor:
    "K正規化を行うVisitor"

    def visit(self, env, e):
        method = "visit_" + e.__class__.__name__
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Const(self, env, e):
        if e.typ == types.Unit:
            return IR("Unit"), types.Unit
        elif e.typ == types.Bool:
            return IR("Int", 1 if e.value else 0), types.Int
        elif e.type == types.Int:
            return IR("Int", e.value), types.Int
        elif e.type == types.Float:
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
            op, ret_typ = "Neg", types.Int
        elif e.op == "-.":
            op, ret_typ = "FNeg", types.Float
        else:
            raise ValueError(f"unknown operator '{e.op}'")

        e1, t1 = self.visit(self.arg)
        if isinstance(e1, syntax.Var):
            return IR(op, e1.name), ret_typ
        else:
            x = gen_tmp_id(t1)
            e2 = IR(op, x)
            return IR("Let", (x, t1), e1, e2), ret_typ

    def visit_BinaryExp(self, env, e):
        if e.op == "+":
            op, ret_typ = "Add", types.Int
        elif e.op == "-":
            op, ret_typ = "Sub", types.Int
        elif e.op == "+.":
            op, ret_typ = "FAdd", types.Float
        elif e.op == "-.":
            op, ret_typ = "FSub", types.Float
        elif e.op == "*.":
            op, ret_typ = "FMul", types.Float
        elif e.op == "/.":
            op, ret_typ = "FDiv", types.Float
        else:
            raise ValueError(f"unknown operator '{e.op}'")

        e1, t1 = self.visit(env, e.left)
        e2, t2 = self.visit(env, e.right)
        if isinstance(e1, syntax.Var) and isinstance(e2, syntax.Var):
            return IR(op, e1.name, e2.name), ret_typ
        elif isinstance(e1, syntax.Var):
            x = gen_tmp_id(t2)
            e3 = IR(op, e1.name, x)
            return IR("Let", (x, t2), e2, e3), ret_typ
        elif isinstance(e2, syntax.Var):
            x = gen_tmp_id(t1)
            e3 = IR(op, x, e2.name)
            return IR("Let", (x, t1), e1, e3), ret_typ
        else:
            x = gen_tmp_id(t1)
            y = gen_tmp_id(t2)
            e3 = IR(op, x, y)
            return IR("Let", (x, t1), e1, IR("Let", (y, t2), e2, e3)), ret_typ


def normalize(e):
    return KNormalizeVisitor().visit(pmap(), e)
