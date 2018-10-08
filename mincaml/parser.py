import ply.lex as lex
import ply.yacc as yacc

from . import syntax
from . import types
from .id import gen_tmp_id


tokens = (
    "BOOL",
    "INT",
    "FLOAT",
    "NOT",
    "MINUS",
    "PLUS",
    "MINUS_DOT",
    "PLUS_DOT",
    "AST_DOT",
    "SLASH_DOT",
    "EQUAL",
    "LESS_GREATER",
    "LESS_EQUAL",
    "GREATER_EQUAL",
    "LESS",
    "GREATER",
    "IF",
    "THEN",
    "ELSE",
    "IDENT",
    "LET",
    "IN",
    "REC",
    "COMMA",
    "ARRAY_CREATE",
    "DOT",
    "LESS_MINUS",
    "SEMICOLON",
    "LPAREN",
    "RPAREN",
    # "EOF",
)

t_ARRAY_CREATE = r"Array\.(create|make)"
t_MINUS = r"-"
t_PLUS = r"\+"
t_MINUS_DOT = r"-\."
t_PLUS_DOT = r"\+\."
t_AST_DOT = r"\*\."
t_SLASH_DOT = r"/\."
t_EQUAL = r"="
t_LESS_GREATER = r"<>"
t_LESS_EQUAL = r"<="
t_GREATER_EQUAL = r">="
t_LESS = r"<"
t_GREATER = r">"
t_COMMA = r","
t_DOT = r"\."
t_LESS_MINUS = r"<-"
t_SEMICOLON = r";"
t_LPAREN = r"\("
t_RPAREN = r"\)"
# t_EOF = r""


reserved = {
    "not": "NOT",
    "if": "IF",
    "then": "THEN",
    "else": "ELSE",
    "let": "LET",
    "in": "IN",
    "rec": "REC",
}


def t_IDENT(t):
    r"[a-z][_a-zA-Z0-9]*"
    t.type = reserved.get(t.value, "IDENT")  # Check for reserved words
    return t


def t_BOOL(t):
    r"true|false"
    t.value = bool(t.value)
    return t


def t_INT(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_FLOAT(t):
    r"\d+(\.\d*)?([eE][+-]?\d+)?"
    t.value = float(t.value)
    return t


# Define a rule so we can track line numbers
def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


# A string containing ignored characters (spaces and tabs)
t_ignore = " \t\r"


# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


start = "exp"

precedence = (
    ("nonassoc", "IN"),
    ("right", "prec_let"),
    ("right", "SEMICOLON"),
    ("right", "prec_if"),
    ("right", "LESS_MINUS"),
    ("nonassoc", "prec_tuple"),
    ("left", "COMMA"),
    ("left", "EQUAL", "LESS_GREATER", "LESS", "GREATER", "LESS_EQUAL", "GREATER_EQUAL"),
    ("left", "PLUS", "MINUS", "PLUS_DOT", "MINUS_DOT"),
    ("left", "AST_DOT", "SLASH_DOT"),
    ("right", "prec_unary_minus"),
    ("left", "prec_app"),
    ("left", "DOT"),
)


def p_simple_exp(p):
    "exp : simple_exp"
    p[0] = p[1]


def p_exp_group(p):
    "simple_exp : LPAREN exp RPAREN"
    p[0] = p[2]


def p_unit(p):
    "simple_exp : LPAREN RPAREN"
    p[0] = syntax.Const(types.Unit, None)


def p_bool(p):
    "simple_exp : BOOL"
    p[0] = syntax.Const(types.Bool, p[1])


def p_int(p):
    "simple_exp : INT"
    p[0] = syntax.Const(types.Int, p[1])


def p_float(p):
    "simple_exp : FLOAT"
    p[0] = syntax.Const(types.Float, p[1])


def p_var(p):
    "simple_exp : IDENT"
    p[0] = syntax.Var(p[1])


def p_array_get(p):
    "simple_exp : simple_exp DOT LPAREN exp RPAREN"
    p[0] = syntax.Get(p[1], p[4])


def p_not(p):
    "exp : NOT exp %prec prec_app"
    p[0] = syntax.UnaryExp("not", p[2])


def p_uminus(p):
    "exp : MINUS exp %prec prec_unary_minus"
    p[0] = syntax.UnaryExp("-", p[2])


def p_binary_exp(p):
    """exp : exp PLUS exp
           | exp MINUS exp
           | exp EQUAL exp
           | exp LESS_GREATER exp
           | exp LESS exp
           | exp GREATER exp
           | exp LESS_EQUAL exp
           | exp GREATER_EQUAL exp
           | exp PLUS_DOT exp
           | exp MINUS_DOT exp
           | exp AST_DOT exp
           | exp SLASH_DOT exp
    """
    # 比較演算子の書き換えをこのパスでは行わない(mincamlと異なる挙動)
    p[0] = syntax.BinaryExp(p[1], p[2], p[3])


def p_if(p):
    "exp : IF exp THEN exp ELSE exp  %prec prec_if"
    p[0] = syntax.If(p[2], p[4], p[6])


def p_let(p):
    "exp : LET IDENT EQUAL exp IN exp  %prec prec_let"
    p[0] = syntax.Let(types.Var(), p[2], p[4], p[6])


def p_let_rec(p):
    "exp : LET REC fundef IN exp  %prec prec_let"
    p[0] = syntax.LetRec(p[3], p[5])


def p_fun_app(p):
    "exp : simple_exp actual_args  %prec prec_app"
    p[0] = syntax.App(p[1], p[2])


def p_tuple(p):
    "exp : elems  %prec prec_tuple"
    p[0] = syntax.Tuple(p[1])


def p_let_tuple(p):
    "exp : LET LPAREN pat RPAREN EQUAL exp IN exp"
    p[0] = syntax.LetTuple(p[3], p[6], p[7])


def p_array_put(p):
    "exp : simple_exp DOT LPAREN exp RPAREN LESS_MINUS exp"
    p[0] = syntax.Put(p[1], p[4], p[7])


def p_semicolon(p):
    "exp : exp SEMICOLON exp"
    p[0] = syntax.Let(types.Unit, gen_tmp_id(types.Unit), p[1], p[3])


def p_array_create(p):
    "exp : ARRAY_CREATE simple_exp simple_exp  %prec prec_app"
    p[0] = syntax.Array(p[2], p[3])


def p_funcdef(p):
    "fundef : IDENT formal_args EQUAL exp"
    p[0] = syntax.FunDef(p[1], p[2], p[4])


def p_formal_args(p):
    """formal_args : IDENT formal_args
                   | IDENT
    """
    if len(p) == 2:
        p[0] = [(p[1], types.Var())]
    else:
        p[0] = [(p[1], types.Var())] + p[2]


def p_actual_args(p):
    """actual_args : actual_args simple_exp  %prec prec_app
                   | simple_exp  %prec prec_app
    """
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]


def p_elems(p):
    """elems : elems COMMA exp
             | exp COMMA exp
    """
    if isinstance(p[1], list):
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1], p[3]]


def p_pat(p):
    """pat : pat COMMA IDENT
           | IDENT COMMA IDENT
    """
    if isinstance(p[1], list):
        p[0] = p[1] + [(p[3], types.Var())]
    else:
        p[0] = [(p[1], types.Var()), (p[3], types.Var())]


def p_error(p):
    print(f"syntax error at '{p.value}'")


# Build the lexer and parser
lexer = lex.lex()
parser = yacc.yacc()


if __name__ == "__main__":
    while True:
        try:
            s = input("> ")
        except EOFError:
            break
        if not s:
            continue
        yacc.parse(s)
