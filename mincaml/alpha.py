from pyrsistent import pmap

from .id import gen_id
from .knorm import FunDef


class AlphaVisitor:
    def visit(self, env, e):
        method = "visit_" + e[0]
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Unit(self, env, e):
        return e

    def visit_Int(self, env, e):
        return e

    def visit_Float(self, env, e):
        return e

    def visit_Neg(self, env, e):
        return [e[0], env[e[1]]]

    def visit_Add(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_Sub(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_FNeg(self, env, e):
        return [e[0], env[e[1]]]

    def visit_FAdd(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_FSub(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_FMul(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_FDiv(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_IfEq(self, env, e):
        return [
            e[0],
            env[e[1]],
            env[e[2]],
            self.visit(env, e[3]),
            self.visit(env, e[4]),
        ]

    def visit_IfLE(self, env, e):
        return [
            e[0],
            env[e[1]],
            env[e[2]],
            self.visit(env, e[3]),
            self.visit(env, e[4]),
        ]

    def visit_Let(self, env, e):
        letenv = {name: gen_id(name) for name in e[1].keys()}
        e_1 = (
            {letenv[name]: (self.visit(env, e1), t) for name, (e1, t) in e[1].items()},
        )
        print("FFF", e[2])
        e_2 = self.visit(env.update(letenv), e[2])
        return [e[0], e_1, e_2]

    def visit_Var(self, env, e):
        return [e[0], env[e[1]]]

    def visit_LetRec(self, env, e):
        fundef = e[1]
        new_env1 = env.set(fundef.name, gen_id(fundef.name))
        new_env2 = new_env1.update({name: gen_id(name) for name, _ in fundef.args})
        # print(fundef.body)
        self.visit(new_env2, fundef.body)
        return [
            e[0],
            FunDef(
                typ=fundef.typ,
                name=new_env1[fundef.name],
                args=[(new_env2[name], t) for name, t in fundef.args],
                body=self.visit(new_env2, fundef.body),
            ),
            self.visit(new_env1, e[2]),
        ]

    def visit_App(self, env, e):
        return [e[0], env[e[1]], [env[arg] for arg in e[2]]]

    def visit_Tuple(self, env, e):
        return [e[0], [env[name] for name in e[1]]]

    def visit_LetTuple(self, env, e):
        new_env = env.update({name: gen_id(name) for name, _ in e[1]})
        return [
            e[0],
            [(new_env[name], t) for name, t in e[1]],
            env[e[2]],
            self.visit(new_env, e[3]),
        ]

    def visit_Get(self, env, e):
        return [e[0], env[e[1]], env[e[2]]]

    def visit_Put(self, env, e):
        return [e[0], env[e[1]], env[e[2]], env[e[3]]]

    def visit_ExtArray(self, env, e):
        return e

    def visit_ExtFunApp(self, env, e):
        return [e[0], e[1], [env[arg] for arg in e[2]]]


def conversion(e):
    return AlphaVisitor().visit(pmap(), e)
