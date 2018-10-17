from . import types

tmp_cnt = 0


def _inc():
    global tmp_cnt
    tmp_cnt += 1


def reset():
    global tmp_cnt
    tmp_cnt = 0


def gen_id(s):
    _inc()
    return f"{s}.{tmp_cnt}"


def gen_tmp_id(t):
    _inc()
    return "T{}{}".format(id_of_typ(t), tmp_cnt)


def id_of_typ(t):
    if types.is_unit(t):
        return "u"
    elif types.is_bool(t):
        return "b"
    elif types.is_int(t):
        return "i"
    elif types.is_float(t):
        return "d"
    elif types.is_fun(t):
        return "f"
    elif types.is_tuple(t):
        return "t"
    elif types.is_array(t):
        return "a"
    else:
        raise ValueError(f"unknown type {t}")
