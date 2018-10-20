from . import types


class Const:
    def __init__(self, typ, value):
        self.typ = typ
        self.value = value

    def children(self):
        return []


class Var:
    def __init__(self, name):
        self.name = name

    def children(self):
        return []


class UnaryExp:
    def __init__(self, op, arg):
        self.op = op
        self.arg = arg

    def children(self):
        return [self.arg]


class BinaryExp:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

    def children(self):
        return [self.left, self.right]


class Let:
    def __init__(self, typ, name, bound, body):
        self.typ = typ
        self.name = name
        self.bound = bound
        self.body = body

    def children(self):
        return [self.bound, self.body]


class LetRec:
    def __init__(self, fundef, body):
        self.fundef = fundef
        self.body = body

    def children(self):
        return [self.fundef, self.body]


class Fundef:
    def __init__(self, name, args, body):
        self.typ = types.Var()
        self.name = name
        self.args = args
        self.body = body

    def children(self):
        return [self.body]


class LetTuple:
    def __init__(self, pat, bound, body):
        self.pat = pat
        self.bound = bound
        self.body = body

    def children(self):
        return [self.bound, self.body]


class If:
    def __init__(self, cond, then, else_):
        self.cond = cond
        self.then = then
        self.else_ = else_

    def children(self):
        return [self.cond, self.then, self.else_]


class Get:
    def __init__(self, array, index):
        self.array = array
        self.index = index

    def children(self):
        return [self.array, self.index]


class Put:
    def __init__(self, array, index, exp):
        self.array = array
        self.index = index
        self.exp = exp

    def children(self):
        return [self.array, self.index, self.exp]


class Array:
    def __init__(self, len, init):
        self.len = len
        self.init = init

    def children(self):
        return [self.len, self.init]


class Tuple:
    def __init__(self, elems):
        self.elems = elems

    def children(self):
        return self.elems


class App:
    def __init__(self, fun, args):
        self.fun = fun
        self.args = args

    def children(self):
        return [self.fun] + self.args
