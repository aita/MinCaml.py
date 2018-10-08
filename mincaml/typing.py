from pyrsistent import pmap
from . import logger
from . import types


class UnifyError(Exception):
    def __init__(self, t1, t2):
        self.t1 = t1
        self.t2 = t2
        super().__init__(f"cannot unify {t1} and {t2}")


class TypingVisitor:
    "抽象構文木をたどり型推論を行うVisitorクラス"

    def __init__(self, extenv):
        self.extenv = extenv

    def visit(self, env, e):
        method = "visit_" + e.__class__.__name__
        visitor = getattr(self, method)
        return visitor(env, e)

    def visit_Const(self, env, e):
        return e.typ

    def visit_Var(self, env, e):
        if e.name in env:
            # unify(e.typ, env[e.name])
            return env[e.name]
        elif e.name in self.extenv:
            # unify(e.typ, self.extenv[e.name])
            return self.extenv[e.name]
        else:
            logger.warn(f"free variable {e.name} assumed as external.")
            t = types.Var()
            self.extenv[e.name] = t
            # e.typ = t  # 外部変数の型変数を代入(mincamlにはない挙動)
            return t

    def visit_UnaryExp(self, env, e):
        op = e.op
        if op == "not":
            unify(types.Bool, self.visit(e.arg))
            return types.Bool
        elif op == "-":
            unify(types.Int, self.visit(e.arg))
            return types.Int
        elif op == "-.":
            unify(types.Float, self.visit(e.arg))
            return types.Float
        else:
            raise ValueError(f"unknown unary operator: {op}")

    def visit_BinaryExp(self, env, e):
        op = e.op
        if op in ("+", "-"):
            unify(types.Int, self.visit(env, e.left))
            unify(types.Int, self.visit(env, e.right))
            return types.Int
        elif op in ("+.", "-.", "*.", "/."):
            unify(types.Float, self.visit(env, e.left))
            unify(types.Float, self.visit(env, e.right))
            return types.Float
        elif op in ("=", "<>", "<=", ">=", "<", ">"):
            unify(self.visit(env, e.left), self.visit(env, e.right))
            return types.Bool
        else:
            raise ValueError(f"unknown binary operator: {op}")

    def visit_Let(self, env, e):
        unify(e.typ, self.visit(env, e.bound))
        return self.visit(env.set(e.name, e.typ), e.body)

    def visit_LetRec(self, env, e):
        env = env.set(e.fundef.name, e.fundef.typ)
        unify(
            e.fundef.typ,
            types.Fun(
                [typ for _, typ in e.fundef.args],
                self.visit(
                    env.update({name: typ for name, typ in e.fundef.args}), e.fundef.exp
                ),
            ),
        )
        return self.visit(env, e.body)

    def visit_LetTuple(self, env, e):
        unify(types.Tuple([typ for _, typ in e.pat]), self.visit(env, self.bound))
        return self.visit(env.update({name: typ for name, typ in e.pat}), e.body)

    def visit_If(self, env, e):
        unify(self.visit(env, e.cond), types.Bool)
        t1 = self.visit(env, e.then)
        t2 = self.visit(env, e.else_)
        unify(t1, t2)
        return t1

    def visit_Tuple(self, env, e):
        return types.Tuple([self.visitor(env, e) for e in e.elems])

    def visit_Array(self, env, e):
        unify(self.visit(env, e.len), types.Int)
        return types.Array(self.visit(env.e.init))

    def visit_Get(self, env, e):
        t = types.Var()
        unify(types.Array(t), self.visit(env, e.array))
        unify(types.Int, self.visit(env, e.index))
        return t

    def visit_Put(self, env, e):
        t = types.Var()
        unify(types.Array(t), self.visit(env, e.array))
        unify(types.Int, self.visit(env, e.index))
        return types.Unit

    def visit_App(self, env, e):
        t = types.Var()
        unify(
            self.visit(env, e.fun),
            types.Fun([self.visit(env, arg) for arg in e.args], t),
        )
        return t


def unify(t1, t2):
    "型が合うように、型変数への代入をする"
    if t1 == t2 and t1 in (types.Unit, types.Bool, types.Int, types.Float):
        return

    if types.is_fun(t1) and types.is_fun(t2):
        if len(t1.args) != len(t2.args):
            raise UnifyError(t1, t2)
        for t1_, t2_ in zip(t1.args, t2.args):
            unify(t1_, t2_)
        unify(t1.ret, t2.ret)
        return

    if types.is_tuple(t1) and types.is_tuple(t2):
        if len(t1.elems) != len(t2.elems):
            raise UnifyError(t1, t2)
        for t1_, t2_ in zip(t1.elems, t2.elems):
            unify(t1_, t2_)
        return

    if types.is_array(t1) and types.is_array(t2):
        unify(t1.elem, t2.elem)
        return

    if types.is_var(t1) and types.is_var(t2) and t1.ref == t2.ref:
        return
    elif types.is_var(t1) and t1.ref.contents:
        unify(t1.ref.contents, t2)
        return
    elif types.is_var(t2) and t2.ref.contents:
        unify(t1, t2.ref.contents)
        return
    elif types.is_var(t1) and t1.ref.contents is None:
        if occurs_check(t1.ref, t2):
            raise UnifyError(t1, t2)
        t1.ref.contents = t2
        return
    elif types.is_var(t2) and t2.ref.contents is None:
        if occurs_check(t2.ref, t1):
            raise UnifyError(t1, t2)
        t2.ref.contents = t1
        return

    raise UnifyError(t1, t2)


def occurs_check(r1, t2):
    "出現検査: 型t2の中に型変数の参照r1が現れるかチェック"
    if types.is_fun(t2):
        return any(occurs_check(r1, t) for t in t2.args) or occurs_check(r1, t2.ret)
    elif types.is_tuple(t2):
        return any(occurs_check(r1, t) for t in t2.elems)
    elif types.is_array(t2):
        return occurs_check(r1, t2.elem)
    elif types.is_var(t2):
        r2 = t2.ref
        if r1 == r2:
            return True
        elif r2.contents is None:
            return False
        elif r2.contents is not None:
            return occurs_check(r1, r2.contents)
    return False


class DerefVisitor:
    def visit(self, e):
        method = "visit_" + e.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor(e)

    def generic_visit(self, e):
        for c in e.children():
            self.visit(c)

    def visit_Let(self, e):
        e.typ = deref_typ(e.typ)
        self.visit(e.bound)
        self.visit(e.body)

    def visit_LetRec(self, e):
        e.fundef.typ = deref_typ(e.fundef.typ)
        e.fundef.args = [(name, deref_typ(arg)) for name, arg in e.fundef.args]
        self.visit(e.body)

    def visit_LetTuple(self, e):
        e.pat = [(name, deref_typ(t)) for name, t in e.pat]
        self.visit(e.bound)
        self.visit(e.body)


def deref_typ(t):
    if types.is_fun(t):
        return types.Fun([deref_typ(x) for x in t.args], deref_typ(t.ret))
    elif types.is_tuple(t):
        return types.Tuple([deref_typ(x) for x in t.elems])
    elif types.is_array(t):
        return types.Array(deref_typ(t.elem))
    elif types.is_var(t) and t.ref is None:
        logger.warn("uninstantiated type variable detected; assuming int.")
        t.ref.contents = types.Int
        return types.Int
    elif types.is_var(t) and t.ref is not None:
        t2 = deref_typ(t.ref.contents)
        t.ref.contents = t2
        return t2
    return t


def deref_term(e):
    DerefVisitor().visit(e)


def typing(e):
    visitor = TypingVisitor({})
    try:
        unify(types.Unit, visitor.visit(pmap(), e))
    except UnifyError:
        raise ValueError("top level does not have type unit")
    deref_term(e)
