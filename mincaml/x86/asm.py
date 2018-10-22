from collections import namedtuple


REGS = ("%eax", "%ebx", "%ecx", "%edx", "%esi", "%edi")
REG_SP = "%ebp"
REG_HP = "min_caml_hp"


def V(id):
    return ("V", id)


def C(i):
    return ("C", i)


def Ans(*args):
    return ("Ans", args)


def Let(xt, e1, e2):
    return ("Let", xt, e1, e2)


def align(i):
    if i % 8 == 0:
        return i
    else:
        # return i + 4
        return ((i - 1) // 8 + 1) * 8


def free_variables(e):
    name = e[0]
    if name == "Ans":
        return free_variables(e[1])
    elif name == "Let":
        (x, t), e1, e2 = e[1:]
        return free_variables(e1) | {x} | free_variables(e2)
    elif name in ("Nop", "Set", "SetL", "Comment", "Restore"):
        return set()
    elif name in ("Mov", "Neg", "FMovD", "FNegD", "Save"):
        return {e[1]}
    elif name in ("Add", "Sub", "Ld", "LdDF"):
        x, y = e[1], e[2]
        return {x} | fv_id_or_imm(y)
    elif name in ("St", "StDF"):
        x, y, z = e[1], e[2], e[3]
        return {x, y} | fv_id_or_imm(z)
    elif name in ("FAddD", "FSubD", "FMulD", "FDivD"):
        x, y = e[1], e[2]
        return {x, y}
    elif name in ("IfEq", "IfLE", "IfGE"):
        x, y, e1, e2 = e[1:]
        return {x} | fv_id_or_imm(y) | free_variables(e1) | free_variables(e2)
    elif name in ("IfFEq", "IfFLE"):
        x, y, e1, e2 = e[1:]
        return {x, y} | free_variables(e1) | free_variables(e2)
    elif name == "CallCls":
        x, ys, zs = e[1:]
        return {x} | set(ys) | set(zs)
    elif name == "CallDir":
        ys, zs = e[2], e[3]
        return set(ys) | set(zs)
    else:
        raise ValueError(f"unknown expression {e}")


def fv_id_or_imm(e):
    if e[0] == "V":
        return {e[1]}
    else:
        return set()


Fundef = namedtuple("Fundef", "name args fargs body ret")
