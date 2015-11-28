# -*- coding: utf-8 -*-
from comptests.registrar import comptest
from contracts import contract
from mocdp.posets.find_poset_minima.baseline_n2 import (poset_minima,
    poset_minima_n2)
from mocdp.posets.nat import Nat
from mocdp.posets.poset import Poset
from mocdp.posets.poset_product import PosetProduct
import random
from mocdp.posets.rcomp import Rcomp
import numpy as np

@contract(n='>=1', ndim='>=1', m='>0')
def get_random_points(n, ndim, m):
    """ Gets a set of n points in [0,m]*[0,m]*... (ndim dimensions) """
    res = set()
    while len(res) < n:
        s = []
        for _ in range(ndim):
            # x = random.randint(0, m)
            x = np.random.rand() * m
            s.append(x)
        r = tuple(s)
        res.add(r)
    return res


@contract(P=Poset, xs='set')
def stats_for_poset_minima(P, xs, f, maxleq=10000):
    """
        
        f(P, x)
    """
    class P2():
        def __init__(self, P):
            self.P = P
            self.nleq = 0
            self.nleq_true = 0
            self.nleq_false = 0

        def leq(self, a, b):
            res = self.P.leq(a, b)
            if res:
                self.nleq_true += 1
            else:
                self.nleq_false += 1
            self.nleq += 1
            if self.nleq >= maxleq:
                msg = ('%d leqs (true: %d, false: %d)' % (self.nleq, self.nleq_true,
                                                                   self.nleq_false))
                raise ValueError(msg)
            return res

        def __getattr__(self, method_name):
            return getattr(P, method_name)

    P_ = P2(P)
    xs_ = list(xs)
    random.shuffle(xs_)
    res = f(P_, xs_)

    print('n: %d' % len(xs))
    print('nres: %d' % len(res))
    print('nleq:  %d' % P_.nleq)
    print('nleqt: %d' % P_.nleq_true)
    print('nleqf: %d' % P_.nleq_false)

    return res



@comptest
def pmin1():
    n = 1000
    ndim = 3
    m = 430000
    Ps = get_random_points(n, ndim, m)
    Pbase = Rcomp()
    N2 = PosetProduct((Pbase,) * ndim)

    method = poset_minima_n2
    r = stats_for_poset_minima(N2, Ps, method)
    print r

#
# def get_random_antichain(n, point_generation, leq):
#     cur = set()
#     while len(cur) < n:
#         print('Current size: %d < %d' % (len(cur), n))
#         remaining = n - len(cur)
#         Ps = point_generation(n * 10)
#         cur.update(Ps)
#         cur = poset_minima(cur, leq)
#     return cur

def get_random_antichain(n, ndim):
    if ndim != 2:
        raise NotImplementedError()
    
    xs = np.linspace(0, 100, n)
    deltas = np.random.rand(n)
    ys = 1.0 / np.cumsum(deltas)
    return zip(xs, ys)


@comptest
def pmin2():
    n = 1000
    ndim = 2
    Pbase = Rcomp()
    N2 = PosetProduct((Pbase,) * ndim)

    print('Using random antichain')
    # point_generation = lambda n: get_random_points(n, ndim, m)
    # Ps = get_random_antichain(n, point_generation, N2.leq)
    Ps = get_random_antichain(n, ndim)
    method = poset_minima_n2
    r = stats_for_poset_minima(N2, Ps, method)
    print r


@comptest
def pmin3():
    pass


@comptest
def pmin4():
    pass


@comptest
def pmin5():
    pass


@comptest
def pmin6():
    pass


@comptest
def pmin7():
    pass


@comptest
def pmin8():
    pass


@comptest
def pmin9():
    pass
