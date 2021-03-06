# -*- coding: utf-8 -*-
import warnings

from contracts.utils import raise_wrapped

from comptests.registrar import comptest
from mcdp import logger, MCDPConstants
from mcdp_dp import NotSolvableNeedsApprox
from mcdp_dp.dp_transformations import get_dp_bounds
from mcdp_lang.parse_interface import parse_poset
from mcdp_posets import LowerSets, UpperSets, NotBelongs, PosetProduct, Rcomp
from mcdp_posets.utils import poset_check_chain
from mcdp_tests.generation import for_all_dps, primitive_dp_test
from mcdp_utils_indexing import compose_indices, get_id_indices, transform_right_inverse


if MCDPConstants.test_dual01_chain:
    dec = for_all_dps
else:
    warnings.warn('disabled test dual01_chain')
    dec = lambda x: x

@dec
def dual01_chain(id_dp, dp):
    try:
        with primitive_dp_test(id_dp, dp):
            print('Starting testing with %r' % id_dp)
            # get a chain of resources
            F = dp.get_fun_space()
            R = dp.get_res_space()
            
            # try to solve
            try: 
                dp.solve(F.witness())
                dp.solve_r(R.witness())
            except NotSolvableNeedsApprox:
                print('NotSolvableNeedsApprox - doing  lower bound ')
                n = 5
                dpL, dpU = get_dp_bounds(dp, nl=n, nu=n)
                dual01_chain(id_dp+'_L%s'%n, dpL)
                dual01_chain(id_dp+'_U%s'%n, dpU)
                return
            
            LF = LowerSets(F)
            UR = UpperSets(R)
        
            rchain = R.get_test_chain(n=8)
            poset_check_chain(R, rchain)
        
            try:
                lfchain = list(map(dp.solve_r, rchain))
                for lf in lfchain:
                    LF.belongs(lf)
            except NotSolvableNeedsApprox as e:
                print('skipping because %s'  % e)
                return
        
            try:
                poset_check_chain(LF, list(reversed(lfchain)))
                
            except ValueError as e:
                msg = 'The results of solve_r() are not a chain.'
                raise_wrapped(Exception, e, msg, chain=rchain, lfchain=lfchain)
        
            # now, for each functionality f, 
            # we know that the corresponding resource should be feasible
            
            for lf, r in zip(lfchain, rchain):
                print('')
                print('r: %s' % R.format(r))
                print('lf = h*(r) = %s' % LF.format(lf))
                
                for f in lf.maximals:
                    print('  f = %s' % F.format(f))
                    f_ur = dp.solve(f)
                    print('  f_ur = h(f) =  %s' % UR.format(f_ur))
                     
                    try:
                        f_ur.belongs(r)
                    except NotBelongs as e:
                        
                        try:
                            Rcomp.tolerate_numerical_errors = True
                            f_ur.belongs(r)
                            logger.info('In this case, there was a numerical error')
                            logger.info('Rcomp.tolerate_numerical_errors = True solved the problem')                    
                        except:
                            msg = ''
                            raise_wrapped(AssertionError, e, msg,
                                          lf=lf, r=r, f_ur=f_ur,
                                          r_repr=r.__repr__(),
                                          f_ur_minimals=f_ur.minimals.__repr__())
    finally:
        Rcomp.tolerate_numerical_errors = False
            
            
@for_all_dps
def dual02(_, dp):
    
    pass

@for_all_dps
def dual03(_, dp):
    pass

@comptest
def test_right_inverse():
    P = parse_poset('((J x W) x s) x (m x Hz)')
    coords = [(1, 1), [(0, 0, 1), (1, 0), (0, 0, 0), (0, 1)]]
    #print 'coords', coords    
    i0 = get_id_indices(P)
    #print 'i0', i0
    # compose
    _i0coords = compose_indices(P, i0, coords, list)

    #print 'i0coords', i0coords

    _Q, _coords2 = transform_right_inverse(P, coords, PosetProduct)
    

