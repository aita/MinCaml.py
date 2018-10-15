from pyrsistent import pmap

from .id import gen_id
from .knorm import FunDef


class AlphaVisitor:
    def visit(self, env, ir):
        method = "visit_" + ir[0]
        visitor = getattr(self, method)
        return visitor(env, ir)

    def visit_Unit(self, env, ir):
        return ir

    def visit_Int(self, env, ir):
        return ir

    def visit_Float(self, env, ir):
        return ir

    def visit_Neg(self, env, ir):
        return [ir[0], env[ir[1]]]

    def visit_Add(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_Sub(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_FNeg(self, env, ir):
        return [ir[0], env[ir[1]]]

    def visit_FAdd(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_FSub(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_FMul(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_FDiv(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_IfEq(self, env, ir):
        return [
            ir[0],
            env[ir[1]],
            env[ir[2]],
            self.visit(env, ir[3]),
            self.visit(env, ir[4]),
        ]

    def visit_IfLE(self, env, ir):
        return [
            ir[0],
            env[ir[1]],
            env[ir[2]],
            self.visit(env, ir[3]),
            self.visit(env, ir[4]),
        ]

    def visit_Let(self, env, ir):
        new_env = {name: gen_id(name) for name in ir[1]}
        return [
            ir[0],
            {new_env[name]: (self.visit(env, e), t) for name, (e, t) in ir[1].items()},
            ir[2],
        ]

    def visit_Var(self, env, ir):
        return [ir[0], env[ir[1]]]

    def visit_LetRec(self, env, ir):
        fundef = ir[1]
        new_env1 = env.set(fundef.name, gen_id(fundef.name))
        new_env2 = new_env1.update({name: gen_id(name) for name, _ in fundef.args})
        return [
            ir[0],
            FunDef(
                typ=fundef.typ,
                name=new_env1[fundef.name],
                args=[(new_env2[name], t) for name, t in fundef.args],
                body=self.visit(new_env2, fundef.body),
            ),
            self.visit(new_env1, ir[2]),
        ]

    def visit_App(self, env, ir):
        return [ir[0], env[ir[1]]] + [env[arg] for arg in ir[2:]]

    def visit_Tuple(self, env, ir):
        return [ir[0]] + [env[name] for name in ir[1:]]

    def visit_LetTuple(self, env, ir):
        new_env = env.update({name: gen_id(name) for name, _ in ir[1]})
        return [
            ir[0],
            [(new_env[name], t) for name, t in ir[1]],
            env[ir[2]],
            self.visit(new_env, ir[3]),
        ]

    def visit_Get(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]]]

    def visit_Put(self, env, ir):
        return [ir[0], env[ir[1]], env[ir[2]], env[ir[3]]]

    def visit_ExtArray(self, env, ir):
        return ir

    def visit_ExtFunApp(self, env, ir):
        return [ir[0], ir[1]] + [env[arg] for arg in ir[2:]]


def conversion(e):
    return AlphaVisitor().visit(pmap(), e)
