from collections import namedtuple

REGS = ("%eax", "%ebx", "%ecx", "%edx", "%esi", "%edi")
REG_SP = "%ebp"
REG_HP = "min_caml_hp"


def V(id):
    return ("V", id)


def C(i):
    return ("C", i)


def Ans(*args):
    return ("Ans", tuple(args))


def Let(xt, e1, e2):
    return ("Let", xt, e1, e2)


def align(i):
    if i % 8 == 0:
        return i
    else:
        # return i + 4
        return ((i - 1) // 8 + 1) * 8


Fundef = namedtuple("Fundef", "name args fargs body ret")
