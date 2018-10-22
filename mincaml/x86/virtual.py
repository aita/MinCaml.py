from pyrsistent import pmap

import functools

# from .. import logger
from ..id import gen_id, gen_tmp_id
from .. import types
from ..closure import free_variables
from .asm import V, C, Ans, Let, REG_HP, align, Fundef


def fletd(x, e1, e2):
    return Let((x, types.Float), e1, e2)


def seq(e1, e2):
    return Let((gen_tmp_id(types.Unit), types.Unit), e1, e2)


def concat(e1, xt, e2):
    if e1[0] == "Ans":
        return Let(xt, e1[1], e2)
    elif e1[0] == "Let":
        yt, exp, new_e1 = e1[1:]
        return Let(yt, exp, concat(new_e1, xt, e2))
    else:
        raise ValueError


def separate(xts):
    int_lst, float_lst = [], []
    for x, t in xts:
        if types.is_float(t):
            float_lst.append(x)
        elif types.is_int(t):
            int_lst.append(x)
    return int_lst, float_lst


def expand(xts, ini, addf, addi):
    def func(a, xt):
        offset, acc = a
        x, t = xt
        if types.is_unit(t):
            return a
        elif types.is_float(t):
            offset = align(offset)
            return offset + 8, addf(x, offset, acc)
        else:
            return offset + 4, addi(x, t, offset, acc)

    return functools.reduce(func, xts, ini)


class Visitor:
    def __init__(self):
        self.data = []  # 定数テーブル

    def visit(self, env, e):
        method = "visit_" + e[0]
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Unit(self, env, e):
        return Ans("Nop")

    def visit_Int(self, env, e):
        return Ans("Set", e[1])

    def visit_Float(self, env, e):
        d = e[1]
        label = None
        # すでに定数テーブルにあったら再利用
        for l, d in self.data:
            if d == e[1]:
                label = l
                break
        if label is None:
            label = gen_id("l")
            self.data.append((label, d))
        x = gen_id("l")
        return Let((x, types.Int), ("SetL", label), Ans("LdDF", x, C(0), 1))

    def visit_Neg(self, env, e):
        return Ans("Neg", e[1])

    def visit_Add(self, env, e):
        x, y = e[1:]
        return Ans("Add", x, V(y))

    def visit_Sub(self, env, e):
        x, y = e[1:]
        return Ans("Sub", x, V(y))

    def visit_FNeg(self, env, e):
        x = e[1]
        return Ans("FNegD", x)

    def visit_FAdd(self, env, e):
        x, y = e[1:]
        return Ans("FAddD", x, y)

    def visit_FSub(self, env, e):
        x, y = e[1:]
        return Ans("FSubD", x, y)

    def visit_FMul(self, env, e):
        x, y = e[1:]
        return Ans("FMulD", x, y)

    def visit_FDiv(self, env, e):
        x, y = e[1:]
        return Ans("FDivD", x, y)

    def visit_IfEq(self, env, e):
        x, y, e1, e2 = e[1:]
        t = env[x]
        if types.is_bool(t) or types.is_int(t):
            return Ans("IfEq", x, V(y), self.visit(env, e1), self.visit(env, e2))
        elif types.is_float(t):
            return Ans("IfFEq", x, y, self.visit(env, e1), self.visit(env, e2))
        else:
            raise ValueError("equality supported only for bool, int, and float")

    def visit_IfLE(self, env, e):
        x, y, e1, e2 = e[1:]
        t = env[x]
        if types.is_bool(t) or types.is_int(t):
            return Ans("IfLE", x, V(y), self.visit(env, e1), self.visit(env, e2))
        elif types.is_float(t):
            return Ans("IfFLE", x, y, self.visit(env, e1), self.visit(env, e2))
        else:
            raise ValueError("inequality supported only for bool, int, and float")

    def visit_Let(self, env, e):
        (x, t1), e1, e2 = e[1:]
        new_e1 = self.visit(env, e1)
        new_e2 = self.visit(env.set(x, t1), e2)
        return concat(new_e1, (x, t1), new_e2)

    def visit_Var(self, env, e):
        x = e[1]
        t = env[x]
        if types.is_unit(t):
            return Ans("Nop")
        elif types.is_float(t):
            return Ans("FMovD", x)
        else:
            return Ans("Mov", x)

    def visit_MakeCls(self, env, e):
        "クロージャの生成"
        (x, t), (l, ys), e2 = e[1:]
        # Closureのアドレスをセットしてから、自由変数の値をストア
        new_e2 = self.visit(env.set(x, t), e2)
        offset, store_fv = expand(
            [(y, env[y]) for y in ys],
            (4, new_e2),
            lambda y, offset, store_fv: seq(("StDF", y, x, C(offset), 1), store_fv),
            lambda y, _, offset, store_fv: seq(("St", y, x, C(offset), 1), store_fv),
        )
        z = gen_id("l")
        return Let(
            (x, t),
            ("Mov", REG_HP),
            Let(
                (REG_HP, types.Int),
                ("Add", REG_HP, C(align(offset))),
                Let((z, types.Int), ("SetL", l), seq(("St", z, x, C(0), 1), store_fv)),
            ),
        )

    def visit_AppCls(self, env, e):
        x, ys = e[1:]
        int_lst, float_lst = separate([(y, env[y]) for y in ys])
        return Ans("CallCls", x, int_lst, float_lst)

    def visit_AppDir(self, env, e):
        x, ys = e[1:]
        int_lst, float_lst = separate([(y, env[y]) for y in ys])
        return Ans("CallDir", x, int_lst, float_lst)

    def visit_Tuple(self, env, e):
        xs = e[1]
        y = gen_id("t")
        offset, store = expand(
            [(x, env[x]) for x in xs],
            (0, Ans("Mov", y)),
            lambda x, offset, store: seq(("StDF", x, y, C(offset), 1), store),
            lambda x, _, offset, store: seq(("St", x, y, C(offset), 1), store),
        )
        return Let(
            (y, types.Tuple([env[x] for x in xs])),
            ("Mov", REG_HP),
            Let((REG_HP, types.Int), ("Add", REG_HP, C(align(offset))), store),
        )

    def visit_LetTuple(self, env, e):
        xts, y, e2 = e[1:]
        s = free_variables(e2)

        def addf(x, offset, load):
            if x not in s:
                return load
            else:
                return fletd(x, ("LdDF", y, C(offset), 1), load)

        def addi(x, t, offset, load):
            if x not in s:
                return load
            else:
                return Let((x, t), ("Ld", y, C(offset), 1), load)

        _, load = expand(xts, (0, self.visit(env.update(dict(xts)), e2)), addf, addi)
        return load

    def visit_Get(self, env, e):
        x, y = e[1:]
        t = env[x]
        if types.is_array(t):
            if types.is_unit(t.elem):
                return Ans("Nop")
            elif types.is_unit(t.elem):
                return Ans("LdDF", x, V(y), 8)
            else:
                return Ans("Ld", x, V(y), 4)
        else:
            raise (f"cannot get from {t}")

    def visit_Put(self, env, e):
        x, y, z = e[1:]
        t = env[x]
        if types.is_array(t):
            if types.is_unit(t.elem):
                return Ans("Nop")
            elif types.is_unit(t.elem):
                return Ans("StDF", z, x, V(y), 8)
            else:
                return Ans("St", z, x, V(y), 4)
        else:
            raise (f"cannot put into {t}")

    def visit_ExtArray(self, env, e):
        return Ans("SetL", "min_caml_" + e[1])


def gen_funcdef(visitor, closure):
    "関数の仮想マシンコード生成"
    x, t, yts, zts, e = closure
    int_lst, float_lst = separate(yts)
    env = {x: t}
    env.update(dict(zts))
    env.update(dict(yts))
    offset, load = expand(
        zts,
        (4, visitor.visit(pmap(env), e)),
        lambda z, offset, load: fletd(z, ("LdDF", x, C(offset), 1), load),
        lambda z, t, offset, load: Let((z, t), ("Ld", x, C(offset), 1), load),
    )
    if not types.is_fun(t):
        raise ValueError
    return Fundef(x, int_lst, float_lst, load, t.ret)


def generate(prog):
    fundefs, e = prog
    visitor = Visitor()
    fundefs = [gen_funcdef(visitor, f) for f in fundefs]
    e = visitor.visit(pmap(), e)
    return visitor.data, fundefs, e
