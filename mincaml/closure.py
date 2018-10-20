from pyrsistent import pmap
from collections import namedtuple

from . import logger


Closure = namedtuple("Closure", "entry actual_fv")
Fundef = namedtuple("Fundef", "name typ args formal_fv body")


def free_variables(e):
    name = e[0]
    if name in ("Unit", "Int", "Float", "ExtArray"):
        return set()
    elif name in ("Var", "Neg", "FNeg"):
        return {e[1]}
    elif name in ("Add", "Sub", "FAdd", "FSub", "FMul", "FDiv", "Get"):
        return {e[1], e[2]}
    elif name in ("IfEq", "IfLE"):
        x, y, e1, e2 = e[1:]
        return {x, y} | free_variables(e1) | free_variables(e2)
    elif name == "Let":
        (x, t), e1, e2 = e[1:]
        return free_variables(e1) | (free_variables(e2) - {x})
    elif name == "MakeCls":
        (x, t), (l, ys), e = e[1:]
        return (set(ys) | free_variables(e)) - {x}
    elif name == "AppCls":
        x, ys = e[1:]
        return {x} | set(ys)
    elif name == "AppDir":
        return set(e[2])
    elif name == "Tuple":
        return set(e[1])
    elif name == "LetTuple":
        xs, y, e = e[1:]
        return {y} | (free_variables(e) - {x for x, _ in xs})
    elif name == "Put":
        return set(e[1:])
    else:
        raise ValueError(f"unknown expression: {name}")


class Visitor:
    def __init__(self):
        self.toplevel = []

    def visit(self, env, known, e):
        method = "visit_" + e[0]
        if hasattr(self, method):
            visitor = getattr(self, method)
            return visitor(env, known, e)
        else:
            return e

    def visit_IfEq(self, env, known, e):
        x, y, e1, e2 = e[1:]
        return (e[0], x, y, self.visit(env, known, e1), self.visit(env, known, e2))

    def visit_IfLE(self, env, known, e):
        x, y, e1, e2 = e[1:]
        return (e[0], x, y, self.visit(env, known, e1), self.visit(env, known, e2))

    def visit_Let(self, env, known, e):
        (x, t), e1, e2 = e[1:]
        return (
            e[0],
            (x, t),
            self.visit(env, known, e1),
            self.visit(env.set(x, t), known, e2),
        )

    def visit_LetRec(self, env, known, e):
        # 関数定義let rec x y1 ... yn = e1 in e2の場合は、
        # xに自由変数がない(closureを介さずdirectに呼び出せる)
        # と仮定し、knownに追加してe1をクロージャ変換してみる
        (x, t, yts, e1), e2 = e[1], e[2]
        toplevel_backup = self.toplevel[:]
        new_env = env.set(x, t)
        new_known = known | {x}
        new_e1 = self.visit(new_env.update(dict(yts)), new_known, e1)
        # 本当に自由変数がなかったか、変換結果e1'を確認する
        # 注意: e1'にx自身が変数として出現する場合はclosureが必要
        zs = free_variables(new_e1) - {y for y, _ in yts}
        if len(zs) > 0:
            # 駄目だったら状態(toplevelの値)を戻して、クロージャ変換をやり直す
            logger.info(f"free variable(s) {zs} found in function {x}.")
            logger.info(f"function {x} cannot be directly applied in fact.")
            self.toplevel = toplevel_backup
            new_e1 = self.visit(env.update(dict(yts)), known, e1)
        zs = free_variables(new_e1) - ({x} | {y for y, _ in yts})
        zts = [(z, new_env[z]) for z in zs]
        self.toplevel.append(Fundef(x, t, yts, zts, new_e1))
        new_e2 = self.visit(new_env, new_known, e2)
        if x in free_variables(new_e2):
            return ("MakeCls", (x, t), Closure(x, zs), new_e2)
        else:
            logger.info(f"eliminating closure(s) {x}.")
            return new_e2

    def visit_App(self, env, known, e):
        x, ys = e[1:]
        if x in known:
            logger.info(f"directly applying {x}.")
            return ("AppDir", x, ys)
        else:
            return ("AppCls", x, ys)

    def visit_LetTuple(self, env, known, e):
        xts, y, e1 = e[1:]
        return (e[0], xts, y, self.visit(env.update(dict(xts)), known, e1))

    def visit_ExtFunApp(self, env, known, e):
        x, ys = e[1:]
        return ("AppDir", "min_caml_" + x, ys)


def conversion(e):
    visitor = Visitor()
    new_e = visitor.visit(pmap(), set(), e)
    return visitor.toplevel, new_e
