class AssocVisitor:
    def visit(self, e):
        method = "visit_" + e[0]
        if hasattr(self, method):
            visitor = getattr(self, method)
            return visitor(e)
        else:
            return e

    def visit_IfEq(self, e):
        return (e[0], e[1], e[2], self.visit(e[3]), self.visit(e[4]))

    def visit_IfLE(self, e):
        return (e[0], e[1], e[2], self.visit(e[3]), self.visit(e[4]))

    def visit_Let(self, e):
        xt, e1, e2 = e[1], e[2], e[3]

        def _insert(e):
            if e[0] == "Let":
                return ("Let", e[1], e[2], _insert(e[3]))
            elif e[0] == "LetRec":
                return ("LetRec", e[1], _insert(e[2]))
            elif e[0] == "LetTuple":
                return ("LetTuple", e[1], e[2], _insert(e[3]))
            else:
                return ("Let", xt, e, self.visit(e2))

        return _insert(self.visit(e1))

    def visit_LetRec(self, e):
        fundef = e[1]
        return (e[0], fundef._replace(body=self.visit(fundef.body)), self.visit(e[2]))

    def visit_LetTuple(self, e):
        return (e[0], e[1], e[2], self.visit(e[3]))


def nested_let_reduction(e):
    return AssocVisitor().visit(e)
