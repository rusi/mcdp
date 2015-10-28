# -*- coding: utf-8 -*-
from .parts import CDPLanguage
from .utils import parse_action
from compmake.jobs.dependencies import isnamedtupleinstance
from contracts import contract
from contracts.interface import Where
from contracts.utils import indent, raise_desc, raise_wrapped
from mocdp.dp.dp_sum import sum_units
from mocdp.exceptions import DPInternalError, DPSemanticError, DPSyntaxError
from mocdp.lang.namedtuple_tricks import get_copy_with_where
from mocdp.posets import NotBelongs, Space, mult_table
from pyparsing import ParseException, ParseFatalException
import functools
from mocdp.lang.parts import make_list, unwrap_list


CDP = CDPLanguage

def wheredecorator(b):
    def bb(tokens, loc, s):
        where = Where(s, loc)
        try:
            res = b(tokens)
        except DPSyntaxError as e:
            e.where = where
            raise DPSyntaxError(str(e), where=where)
        except DPSemanticError as e:
            if e.where is None:
                e.where = where
            raise DPSemanticError(str(e), where=where)
        except BaseException as e:
            raise_wrapped(DPInternalError, e, "Error while parsing.",
                          where=where.__str__(), tokens=tokens)

        if isinstance(res, CDP.PlusN):
            res = CDP.PlusN(ops=make_list(unwrap_list(res.ops), where))

        if isinstance(res, CDP.MultN):
            res = CDP.MultN(ops=make_list(unwrap_list(res.ops), where))

        if isnamedtupleinstance(res) or isinstance(res, CDP.ValueWithUnits):
            res = get_copy_with_where(res, where=where)

#         else:
#             print('Not adding where to %s' % type(res))
        return res
    return bb

def spa(x, b):
    @parse_action
    def p(tokens, loc, s):
        bb = wheredecorator(b)
        res = bb(tokens, loc, s)
        # if we are here, then it means the parse was succesful
        # we try again

        # not this, it would be recursive
        # x.parseString(s[loc:])

        x2 = x.copy()
        x2.setParseAction()
        # a = x2.parseString(s[loc:])
        loc_end, tokens = x2._parse(s[loc:], 0)
        character_end = loc + loc_end

        if isnamedtupleinstance(res) or isinstance(res, CDP.ValueWithUnits):
            w = res.where
            w2 = Where(w.string, character_end=character_end, character=w.character)
            res = get_copy_with_where(res, where=w2)

        return res
    x.setParseAction(p)

def number_with_unit_parse(t):
    value = t[0]
    _units = t[1]
    units = _units.value
    from mocdp.posets.rcomp import Rcomp
    if isinstance(value, int) and isinstance(units, Rcomp):
        value = float(value)
    try:
        units.belongs(value)
    except NotBelongs:
        msg = 'Value %r does not belong to %s.' % (value, units)
        raise_desc(DPSemanticError, msg)
    res = CDP.ValueWithUnits(value, units)
    return res

def res_shortcut3_parse(tokens):
    name = tokens['name']
    res = []
    for rname in tokens['rnames']:
        res.append(CDP.ResShortcut1(rname, name))
    return CDP.MultipleStatements(res)

def fun_shortcut3_parse(tokens):
    name = tokens['name']
    res = []
    for fname in tokens['fnames']:
        res.append(CDP.FunShortcut1(fname, name))
    return CDP.MultipleStatements(res)

@parse_action
@wheredecorator
def mult_parse_action(tokens):
    tokens = list(tokens[0])

    ops = []
    for i, t in enumerate(tokens):
        if i % 2 == 0:
            ops.append(t)
        else:
            assert t == '*'

    assert len(ops) > 1

    res = CDP.MultN(make_list(ops))
    return res

class MultType():
    def __init__(self, factor):
        self.factor = factor
    def __call__(self, F):
        return mult_table(F, self.factor)

class MultValue():

    def __init__(self, res):
        self.res = res

    def __call__(self, x):
        return x * self.res

def mult_constants2(a, b):
    R = mult_table(a.unit, b.unit)
    value = a.value * b.value
    return CDP.ValueWithUnits(value=value, unit=R)

def mult_constantsN(seq):
    return functools.reduce(mult_constants2, seq)


def add_table(F1, F2):
    if not F1 == F2:
        msg = 'Incompatible units for addition.'
        raise_desc(DPSemanticError, msg, F1=F1, F2=F2)
    return F1

def plus_constants2(a, b):
    R = a.unit 
    Fs = [a.unit, b.unit]
    values = [a.value, b.value]
    res = sum_units(Fs, values, R)
    return CDP.ValueWithUnits(value=res, unit=R)

def plus_constantsN(constants):
    return functools.reduce(plus_constants2, constants)


@parse_action
@wheredecorator
def plus_parse_action(tokens):
    tokens = list(tokens[0])

    ops = []
    for i, t in enumerate(tokens):
        if i % 2 == 0:
            ops.append(t)
        else:
            assert t == '+'
    res = CDP.PlusN(make_list(ops))
    return res


class PlusType():
    @contract(factor=Space)
    def __init__(self, factor):
        self.factor = factor
    def __call__(self, F):
        return add_table(F, self.factor)

class PlusValue():
    def __init__(self, value):
        self.value = value
    def __call__(self, x):
        return x + self.value

@parse_action
def mult_inv_parse_action(tokens):
    tokens = list(tokens[0])

    ops = []
    for i, t in enumerate(tokens):
        if i % 2 == 0:
            ops.append(t)
        else:
            assert t == '*'

    assert len(ops) == 2
    return CDP.InvMult(ops)

def parse_wrap(expr, string):
    # Nice trick: the removE_comments doesn't change the number of lines
    # it only truncates them...
    string0 = remove_comments(string)

    # m = boxit
    m = lambda x: x
    try:
        return expr.parseString(string0, parseAll=True)  # [0]
    except (ParseException, ParseFatalException) as e:
        # ... so we can use "string" here.
        where = Where(string, line=e.lineno, column=e.col)
        raise DPSyntaxError(str(e), where=where)
    except DPSemanticError as e:
        msg = "User error while interpreting the model:"
        msg += "\n\n" + indent(m(string), '  ') + '\n'
        raise_wrapped(DPSemanticError, e, msg, compact=True)
    except DPInternalError as e:
        msg = "Internal error while evaluating the spec:"
        msg += "\n\n" + indent(m(string), '  ') + '\n'
        raise_wrapped(DPInternalError, e, msg, compact=False)

def remove_comments(s):
    lines = s.split("\n")
    def remove_comment(line):
        if '#' in line:
            return line[:line.index('#')]
        else:
            return line
    return "\n".join(map(remove_comment, lines))

# @contract(returns=NamedDP)
def parse_ndp(string):
    from mocdp.lang.syntax import Syntax
    v = parse_wrap(Syntax.dp_rvalue, string)[0]
    from mocdp.lang.blocks import Context, eval_dp_rvalue
    context = Context()
    res = eval_dp_rvalue(v, context)
    # I'm not sure what happens to the context
    # if context.names # error ??

    from mocdp.comp.interfaces import NamedDP
    assert isinstance(res, NamedDP), res
    return res

def parse_line(line):
    from mocdp.lang.syntax import Syntax
    return parse_wrap(Syntax.line_expr, line)[0]
#
# @parse_action
# def dp_model_parse_action(tokens):
#     keyword = tokens[0]
#
#     statements = CDP.MultipleStatements(list(tokens[1:]))
#     print 'statmeents', statements
#     # if not res:
#     #    raise DPSemanticError('Empty model')
# #     from mocdp.lang.blocks import interpret_commands
# #     return interpret_commands(statements)
#
#     return CDP.BuildProblem(keyword=keyword, statements=statements)

def power_expr_parse(t):
    op1 = t[0]
    exp = t[1]
    assert isinstance(exp, CDPLanguage.IntegerFraction)
    return CDP.Power(op1=op1, exponent=exp)

