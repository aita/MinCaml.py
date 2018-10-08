import operator
import functools


class Var:
    class Ref:
        def __init__(self):
            self.contents = None

    def __init__(self):
        self.ref = Var.Ref()

    def __str__(self):
        return f"Var({self.ref.contents})"


class Premitive:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name


class Array:
    def __init__(self, elem):
        self.elem = elem

    def __str__(self):
        return f"Array({self.elem})"


class Tuple:
    def __init__(self, elems):
        self.elems = elems

    def __str__(self):
        return "Tuple({})".format(", ".join(str(t) for t in self.elem_types))


class Fun:
    def __init__(self, args, ret):
        self.args = args
        self.ret = ret

    def __str__(self):
        return "Fun({} -> {})".format(", ".join(str(t) for t in self.args), self.ret)


Unit = Premitive("Unit")
Int = Premitive("Int")
Float = Premitive("Float")
Bool = Premitive("Bool")


def type_func(class_or_tuple):
    def f(instance):
        return isinstance(instance, class_or_tuple)

    return f


is_unit = functools.partial(operator.eq, Unit)
is_int = functools.partial(operator.eq, Int)
is_float = functools.partial(operator.eq, Float)
is_bool = functools.partial(operator.eq, Bool)
is_var = type_func(class_or_tuple=Var)
is_array = type_func(class_or_tuple=Array)
is_tuple = type_func(class_or_tuple=Tuple)
is_fun = type_func(class_or_tuple=Fun)
