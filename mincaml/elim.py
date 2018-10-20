from . import logger
from .knorm import free_variables


def effect(e):
    name = e[0]
    if name == "Let":
        return effect(e[1]) or effect(e[2])
    elif name in ("IfEq", "IfLE"):
        return effect(e[2]) or effect(e[3])
    elif name == "LetRec":
        return effect(e[1])
    elif name == "LetTuple":
        return effect(e[2])
    elif name in ("App", "Put", "ExtFunApp"):
        return True
    else:
        return False


class Visitor:
    def visit(self, e):
        method = "visit_" + e[0]
        if hasattr(self, method):
            visitor = getattr(self, method)
            return visitor(e)
        else:
            return e

    def visit_IfEq(self, e):
        x, y, e1, e2 = e[1:]
        return (e[0], x, y, self.visit(e1), self.visit(e2))

    def visit_IfLE(self, e):
        x, y, e1, e2 = e[1:]
        return (e[0], x, y, self.visit(e1), self.visit(e2))

    def visit_Let(self, e):
        (x, t), e1, e2 = e[1:]
        new_e1 = self.visit(e1)
        new_e2 = self.visit(e2)
        if effect(new_e1) or x in free_variables(new_e2):
            return (e[0], (x, t), new_e1, new_e2)
        else:
            logger.info(f"eliminating variable {x}.")
            return new_e2

    def visit_LetRec(self, e):
        fundef = e[1]
        e2 = self.visit(e[2])
        if fundef.name in free_variables(e2):
            return (e[0], fundef._replace(body=self.visit(fundef.body)), e2)
        else:
            logger.info(f"eliminating variable {fundef.name}.")
            return e2

    def visit_LetTuple(self, e):
        xts, y, e1 = e[1:]
        xs = [x for x, _ in xts]
        new_e1 = self.visit(e1)
        live = free_variables(new_e1)
        if any(x in live for x in xs):
            return (e[0], xts, y, new_e1)
        else:
            logger.info(f"eliminating variables {xs}.")
            return new_e1


def unused_definitions_elimination(e):
    return Visitor().visit(e)
