# -*- coding: utf-8 -*-
r"""Algebra of motivic multiple zeta values

This file contains an implementation of the algebra of motivic
multiple zeta values.

The elements of this algebra are not the usual multiple zeta values as
real numbers defined by concrete iterated integrals, but abstract
symbols that satisfy all the linear relations between formal iterated
integrals that come from algebraic geometry (motivic
relations). Although this set of relations is not explicit, one can
test the equality as explained in the article [Brown2012]_. One can
map these motivic multiple zeta values to the associated real
numbers. Conjecturally, this period map should be injective.

The implementation follows closely all the conventions from [Brown2012]_.

As a convenient abbreviation, the elements will be called multizetas.

EXAMPLES:

One can input multizetas using compositions as arguments::

    sage: Multizeta(3)
    ζ(3)
    sage: Multizeta(2,3,2)
    ζ(2,3,2)

as well as linear combinations of them::

    sage: Multizeta(5)+6*Multizeta(2,3)
    6*ζ(2,3) + ζ(5)

This creates elements of the class :class:`Multizetas`.

One can multiply such elements::

    sage: Multizeta(2)*Multizeta(3)
    6*ζ(1,4) + 3*ζ(2,3) + ζ(3,2)

and their linear combinations::

    sage: (Multizeta(2)+Multizeta(1,2))*Multizeta(3)
    9*ζ(1,1,4) + 5*ζ(1,2,3) + 2*ζ(1,3,2) + 6*ζ(1,4) + 2*ζ(2,1,3) + ζ(2,2,2)
    + 3*ζ(2,3) + ζ(3,1,2) + ζ(3,2)

The algebra is graded by the weight, which is the sum of the arguments. One
can extract homogeneous components::

    sage: z = Multizeta(6)+6*Multizeta(2,3)
    sage: z.homogeneous_component(5)
    6*ζ(2,3)

One can also use the ring of multiple zeta values as a base ring for other
constructions::

    sage: Z = Multizeta
    sage: M = matrix(2,2,[Z(2),Z(3),Z(4),Z(5)])
    sage: M.det()
    -10*ζ(1,6) - 5*ζ(2,5) - ζ(3,4) + ζ(4,3) + ζ(5,2)

.. rubric:: Auxiliary class for alternative notation

One can also use sequences of 0 and 1 as arguments::

    sage: Multizeta(1,1,0)+3*Multizeta(1,0,0)
    I(110) + 3*I(100)

This creates an element of the auxiliary class :class:`Multizetas_iterated`.
This class is used to represent multiple zeta values as iterated integrals.

One can also multiply such elements::

    sage: Multizeta(1,0)*Multizeta(1,0)
    4*I(1100) + 2*I(1010)

Back-and-forth conversion between the two classes can be done using
the methods "composition" and "iterated"::

    sage: (Multizeta(2)*Multizeta(3)).iterated()
    6*I(11000) + 3*I(10100) + I(10010)

    sage: (Multizeta(1,0)*Multizeta(1,0)).composition()
    4*ζ(1,3) + 2*ζ(2,2)

Beware that the conversion between these two classes, besides
exchanging the indexing by words in 0 and 1 and the indexing by
compositions, also involves the sign `(-1)^w` where `w` is the length
of the composition and the number of `1` in the associated word in 0
and 1. For example, one has the equality

.. MATH:: \zeta(2,3,4) = (-1)^3 I(1,0,1,0,0,1,0,0,0).

.. rubric:: Approximate period map

The period map, or rather an approximation, is also available under
the generic numerical approximation method::

    sage: z = Multizeta(5)+6*Multizeta(2,3)
    sage: z.n()
    2.40979014076349
    sage: z.n(prec=100)
    2.4097901407634924849438423801

Behind the scene, all the numerical work is done by the PARI implementation
of numerical multiple zeta values.

.. rubric:: Searching for linear relations

All this can be used to find linear dependencies between any set of
multiple zeta values. Let us illustrate this by an example.

Let us first build our sample set::

    sage: Z = Multizeta
    sage: L = [Z(*c) for c in [(1, 1, 4), (1, 2, 3), (1, 5), (6,)]]

Then one can compute the space of relations::

    sage: M = matrix([Zc.phi_as_vector() for Zc in L])
    sage: K = M.kernel(); K
    Vector space of degree 4 and dimension 2 over Rational Field
    Basis matrix:
    [     1      0     -2   1/16]
    [     0      1      6 -13/48]

and check that the first relation holds::

    sage: relation = L[0]-2*L[2]+1/16*L[3]; relation
    ζ(1,1,4) - 2*ζ(1,5) + 1/16*ζ(6)
    sage: relation.phi()
    0
    sage: relation.is_zero()
    True

.. WARNING::

    Because this code uses an hardcoded multiplicative basis that is
    available up to weight 17 included, some parts will not work
    in larger weights, in particular the test of equality.

REFERENCES:

.. [Brown2012] Francis C. S. Brown, *On the decomposition of motivic
   multiple zeta values*, Advanced Studies in Pure Mathematics 63,
   2012. Galois-Teichmuller Theory and Arithmetic Geometry.

.. [Brown2019] Francis C. S. Brown, *From the Deligne-Ihara conjecture to
   multiple modular values*, :arxiv:`1904.00179`

.. [Deli2012] Pierre Deligne, *Multizêtas, d’après Francis Brown*,
   Séminaire Bourbaki, janvier 2012. http://www.bourbaki.ens.fr/TEXTES/1048.pdf

.. [Stie2020] \S. Stieberger, *Periods and Superstring Amplitudes*,
   Periods in Quantum Field Theory and Arithmetic, Springer Proceedings
   in Mathematics and Statistics 314, 2020
"""
# ****************************************************************************
#       Copyright (C) 2020     Frédéric Chapoton
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#
#                  https://www.gnu.org/licenses/
# ****************************************************************************
from sage.structure.unique_representation import UniqueRepresentation
from sage.algebras.free_zinbiel_algebra import FreeZinbielAlgebra
from sage.arith.misc import bernoulli
from sage.categories.cartesian_product import cartesian_product
from sage.categories.graded_algebras_with_basis import GradedAlgebrasWithBasis
from sage.categories.rings import Rings
from sage.categories.domains import Domains
from sage.combinat.free_module import CombinatorialFreeModule
from sage.combinat.integer_vector import IntegerVectors
from sage.combinat.partition import Partitions
from sage.combinat.words.finite_word import FiniteWord_class
from sage.combinat.words.word import Word
from sage.combinat.words.words import Words
from sage.libs.pari.all import pari
from sage.matrix.constructor import matrix
from sage.misc.cachefunc import cached_function, cached_method
from sage.misc.lazy_attribute import lazy_attribute
from sage.misc.misc_c import prod
from sage.modules.free_module_element import vector
from sage.rings.integer_ring import ZZ
from sage.rings.polynomial.polynomial_ring_constructor import PolynomialRing
from sage.rings.rational_field import QQ
from sage.rings.semirings.non_negative_integer_semiring import NN


# multiplicative generators for weight <= 17
# using the following convention
# (3, 5) <---> (sign) * [1,0,0,1,0,0,0,0]
# taken from the Maple implementation by F. Brown
B_data = [[], [], [(2,)], [(3,)], [], [(5,)], [], [(7,)], [(3, 5)], [(9,)],
          [(3, 7)], [(11,), (3, 3, 5)], [(5, 7), (5, 3, 2, 2)],
          [(13,), (3, 5, 5), (3, 3, 7)], [(5, 9), (3, 11), (3, 3, 3, 5)],
          [(15,), (3, 5, 7), (3, 3, 9), (5, 3, 3, 2, 2)],
          [(11, 5), (13, 3), (5, 5, 3, 3), (7, 3, 3, 3), (7, 5, 2, 2)],
          [(17,), (7, 5, 5), (9, 3, 5), (9, 5, 3), (11, 3, 3),
           (5, 3, 3, 3, 3), (5, 5, 3, 2, 2)]]

Words10 = Words((1, 0), infinite=False)


def coproduct_iterator(paire):
    """
    Return an iterator for terms in the coproduct.

    This is an auxiliary function.

    INPUT:

    - ``paire`` -- a pair (list of indices, end of word)

    OUTPUT:

    iterator for terms in the motivic coproduct

    Each term is seen as a list of positions.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import coproduct_iterator
        sage: list(coproduct_iterator(([0],[0,1,0,1])))
        [[0, 1, 2, 3], [0, 3]]
        sage: list(coproduct_iterator(([0],[0,1,0,1,1,0,1])))
        [[0, 1, 2, 3, 4, 5, 6],
         [0, 1, 2, 6],
         [0, 1, 5, 6],
         [0, 3, 4, 5, 6],
         [0, 4, 5, 6],
         [0, 6]]
    """
    head, tail = paire
    n = len(tail)
    if n == 1:
        yield head
        return
    start_value = tail[0]
    last_index = head[-1]
    yield from coproduct_iterator((head + [last_index + 1], tail[1:]))
    for step in range(3, n):
        if tail[step] != start_value:
            yield from coproduct_iterator((head + [last_index + step],
                                           tail[step:]))


def composition_to_iterated(w, reverse=False):
    """
    Convert a composition to a word in 0 and 1.

    By default, the chosen convention maps (2,3) to (1,0,1,0,0),
    respecting the reading order from left to right.

    The inverse map is given by :func:`iterated_to_composition`.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import composition_to_iterated
        sage: composition_to_iterated((1,2))
        (1, 1, 0)
        sage: composition_to_iterated((3,1,2))
        (1, 0, 0, 1, 1, 0)
        sage: composition_to_iterated((3,1,2,4))
        (1, 0, 0, 1, 1, 0, 1, 0, 0, 0)

    TESTS::

        sage: composition_to_iterated((1,2), True)
        (1, 0, 1)
    """
    word = tuple([])
    loop_over = reversed(w) if reverse else w
    for letter in loop_over:
        word += (1,) + (0,) * (letter - 1)
    return word


def iterated_to_composition(w, reverse=False):
    """
    Convert a word in 0 and 1 to a composition.

    By default, the chosen convention maps (1,0,1,0,0) to (2,3).

    The inverse map is given by :func:`composition_to_iterated`.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import iterated_to_composition
        sage: iterated_to_composition([1,0,1,0,0])
        (2, 3)
        sage: iterated_to_composition(Word([1,1,0]))
        (1, 2)
        sage: iterated_to_composition(Word([1,1,0,1,1,0,0]))
        (1, 2, 1, 3)

    TESTS::

        sage: iterated_to_composition([1,0,1,0,0], True)
        (3, 2)
    """
    b = []
    count = 1
    for letter in reversed(w):
        if letter == 0:
            count += 1
        else:
            b.append(count)
            count = 1
    return tuple(b) if reverse else tuple(reversed(b))


def dual_composition(c):
    """
    Return the dual composition of ``c``.

    This is an involution on compositions such that associated
    multizetas are equal.

    INPUT:

    - ``c`` -- a composition

    OUTPUT:

    a composition

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import dual_composition
        sage: dual_composition([3])
        (1, 2)
        sage: dual_composition(dual_composition([3,4,5])) == (3,4,5)
        True
    """
    i = composition_to_iterated(c)
    ri = [1 - x for x in reversed(i)]
    return iterated_to_composition(ri)


def minimize_term(w, cf):
    """
    Return the largest among ``w`` and the dual word of ``w``.

    INPUT:

    - ``w`` -- a word in the letters 0 and 1

    - ``cf`` -- a coefficient

    OUTPUT:

    (word, coefficient)

    The chosen order is lexicographic with 1 < 0.

    If the dual word is chosen, the sign of the coefficient is changed,
    otherwise the coefficient is returned unchanged.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import minimize_term, Words10
        sage: minimize_term(Words10((1,1,0)), 1)
        (word: 100, -1)
        sage: minimize_term(Words10((1,0,0)), 1)
        (word: 100, 1)
    """
    reverse_w = tuple(1 - t for t in reversed(w))
    for x, y in zip(w, reverse_w):
        if x < y:
            return (w, cf)
        if x > y:
            return (Words10(reverse_w), (-1)**len(w) * cf)
    return (w, cf)


# numerical values

class MultizetaValues(UniqueRepresentation):
    """
    Custom cache for numerical values of multiple zetas.

    Computations are performed using the PARI/GP :pari:`zetamultall` (for the
    cache) and :pari:`zetamult` (for indices/precision outside of the cache).

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import MultizetaValues
        sage: M = MultizetaValues()

        sage: M((1,2))
        1.202056903159594285399738161511449990764986292340...
        sage: parent(M((2,3)))
        Real Field with 1024 bits of precision

        sage: M((2,3), prec=53)
        0.228810397603354
        sage: parent(M((2,3), prec=53))
        Real Field with 53 bits of precision

        sage: M((2,3), reverse=False) == M((3,2))
        True

        sage: M((2,3,4,5))
        2.9182061974731261426525583710934944310404272413...e-6
        sage: M((2,3,4,5), reverse=False)
        0.0011829360522243605614404196778185433287651...

        sage: parent(M((2,3,4,5)))
        Real Field with 1024 bits of precision
        sage: parent(M((2,3,4,5), prec=128))
        Real Field with 128 bits of precision
    """
    def __init__(self):
        """
        When first called, pre-compute up to weight 8 at precision 1024.

        TESTS::

            sage: from sage.modular.multiple_zeta import MultizetaValues
            sage: M = MultizetaValues()
        """
        self.max_weight = 0
        self.prec = 0
        self.reset()

    def __repr__(self):
        r"""
        TESTS::

            sage: from sage.modular.multiple_zeta import MultizetaValues
            sage: MultizetaValues()
            Cached multiple zeta values at precision 1024 up to weight 8
        """
        return "Cached multiple zeta values at precision %d up to weight %d" % (self.prec, self.max_weight)

    def reset(self, max_weight=8, prec=1024):
        r"""
        Reset the cache to its default values or to given arguments.

        TESTS::

            sage: from sage.modular.multiple_zeta import MultizetaValues
            sage: M = MultizetaValues()
            sage: M
            Cached multiple zeta values at precision 1024 up to weight 8
            sage: M.reset(5, 64)
            sage: M
            Cached multiple zeta values at precision 64 up to weight 5
            sage: M.reset()
            sage: M
            Cached multiple zeta values at precision 1024 up to weight 8
        """
        self.prec = int(prec)
        self.max_weight = int(max_weight)
        self._data = pari.zetamultall(self.max_weight, self.prec)

    def update(self, max_weight, prec):
        """
        Compute and store more values if needed.

        TESTS::

            sage: from sage.modular.multiple_zeta import MultizetaValues
            sage: M = MultizetaValues()
            sage: M
            Cached multiple zeta values at precision 1024 up to weight 8
            sage: M.update(5, 64)
            sage: M
            Cached multiple zeta values at precision 1024 up to weight 8
            sage: M.update(5, 2048)
            sage: M
            Cached multiple zeta values at precision 2048 up to weight 8
            sage: M.reset()
        """
        if self.prec < prec or self.max_weight < max_weight:
            self.reset(max(self.max_weight, max_weight), max(self.prec, prec))

    def pari_eval(self, index):
        r"""
        TESTS::

            sage: from sage.modular.multiple_zeta import MultizetaValues
            sage: M = MultizetaValues()
            sage: [M.pari_eval((n,)) for n in range(2,20)]
            [1.64493406684823, 1.20205690315959, 1.08232323371114, 1.03692775514337, ... 1.00000381729326, 1.00000190821272]
        """
        weight = sum(index)
        index = list(reversed(index))
        if weight <= self.max_weight:
            index = pari.zetamultconvert(index, 2)
            return self._data[index - 1]
        else:
            return pari.zetamult(index, precision=self.prec)

    def __call__(self, index, prec=None, reverse=True):
        r"""
        Numerical multiple zeta value as a Sage real floating point number.

        TESTS::

            sage: from sage.modular.multiple_zeta import MultizetaValues
            sage: M = MultizetaValues()
            sage: M((3,2))
            0.7115661975505724320969738060864026120925612044383392364...
            sage: M((3,2), reverse=False)
            0.2288103976033537597687461489416887919325093427198821602...
            sage: M((3,2), prec=128)
            0.71156619755057243209697380608640261209
            sage: M((3,2), prec=128, reverse=False)
            0.22881039760335375976874614894168879193
        """
        if reverse:
            index = list(reversed(index))
        if prec is None:
            prec = self.prec
        weight = sum(index)
        if weight <= self.max_weight and prec <= self.prec:
            index = pari.zetamultconvert(index, 2)
            value = self._data[index - 1]
            return value.sage().n(prec=prec)
        else:
            return pari.zetamult(index, precision=prec).sage().n(prec=prec)


Values = MultizetaValues()


def basis_f_odd_iterator(n):
    """
    Return an iterator over compositions of ``n`` with parts in ``(3,5,7,...)``

    INPUT:

    - ``n`` -- an integer

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import basis_f_odd_iterator
        sage: [list(basis_f_odd_iterator(i)) for i in range(2,9)]
        [[], [(3,)], [], [(5,)], [(3, 3)], [(7,)], [(5, 3), (3, 5)]]
        sage: list(basis_f_odd_iterator(14))
        [(11, 3),
         (5, 3, 3, 3),
         (3, 5, 3, 3),
         (3, 3, 5, 3),
         (9, 5),
         (3, 3, 3, 5),
         (7, 7),
         (5, 9),
         (3, 11)]
    """
    if n == 0:
        yield tuple([])
        return
    if n == 1:
        return
    if n % 2:
        yield (n,)
    for k in range(3, n, 2):
        for start in basis_f_odd_iterator(n - k):
            yield start + (k, )


def basis_f_iterator(n):
    """
    Return an iterator over decompositions of ``n`` using ``2,3,5,7,9,...``.

    The means that each term is made of a power of 2 and a composition
    of the remaining integer with parts in ``(3,5,7,...)``

    INPUT:

    - ``n`` -- an integer

    Each term is returned as a pair (integer, word) where
    the integer is the exponent of 2.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import basis_f_iterator
        sage: [list(basis_f_iterator(i)) for i in range(2,9)]
        [[(1, word: )],
         [(0, word: f3)],
         [(2, word: )],
         [(0, word: f5), (1, word: f3)],
         [(0, word: f3,f3), (3, word: )],
         [(0, word: f7), (1, word: f5), (2, word: f3)],
         [(0, word: f5,f3), (0, word: f3,f5), (1, word: f3,f3), (4, word: )]]
        sage: list(basis_f_iterator(11))
        [(0, word: f11),
         (0, word: f5,f3,f3),
         (0, word: f3,f5,f3),
         (0, word: f3,f3,f5),
         (1, word: f9),
         (1, word: f3,f3,f3),
         (2, word: f7),
         (3, word: f5),
         (4, word: f3)]
    """
    if n < 2:
        return
    for k in range(n // 2 + 1):
        for start in basis_f_odd_iterator(n - 2 * k):
            yield (k, Word(['f{}'.format(d) for d in start]))


def extend_multiplicative_basis(B, n):
    """
    Extend a multiplicative basis into a basis.

    This is an iterator.

    INPUT:

    - ``B`` -- function mapping integer to list of tuples of compositions

    - ``n`` -- an integer

    OUTPUT:

    Each term is a tuple of tuples of compositions.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import extend_multiplicative_basis
        sage: from sage.modular.multiple_zeta import B_data
        sage: list(extend_multiplicative_basis(B_data,5))
        [((5,),), ((3,), (2,))]
        sage: list(extend_multiplicative_basis(B_data,6))
        [((3,), (3,)), ((2,), (2,), (2,))]
        sage: list(extend_multiplicative_basis(B_data,7))
        [((7,),), ((5,), (2,)), ((3,), (2,), (2,))]
    """
    for pi in Partitions(n, min_part=2):
        for liste in cartesian_product([B[i] for i in pi]):
            yield liste


# several classes for the algebra of MZV


def Multizeta(*args):
    r"""
    Common entry point for multiple zeta values.

    If the argument is a sequence of 0 and 1, an element of
    :class:`Multizetas_iterated` will be returned.

    Otherwise, an element of :class:`Multizetas` will be returned.

    The base ring is `\QQ`.

    EXAMPLES::

        sage: Z = Multizeta
        sage: Z(1,0,1,0)
        I(1010)
        sage: Z(3,2,2)
        ζ(3,2,2)

    TESTS::

        sage: Z(3,2,2).iterated().composition()
        ζ(3,2,2)
        sage: Z(1,0,1,0).composition().iterated()
        I(1010)
    """
    if 0 in args:
        return Multizetas_iterated(QQ)(tuple(args))
    return Multizetas(QQ)(tuple(args))


class Multizetas(CombinatorialFreeModule):
    r"""
    Main class for the algebra of multiple zeta values.

    The convention is chosen so that `\zeta(1,2)` is convergent.

    EXAMPLES::

        sage: M = Multizetas(QQ)
        sage: x = M((2,))
        sage: y = M((4,3))
        sage: x+5*y
        ζ(2) + 5*ζ(4,3)
        sage: x*y
        6*ζ(1,4,4) + 8*ζ(1,5,3) + 3*ζ(2,3,4) + 4*ζ(2,4,3) + 3*ζ(3,2,4)
        + 2*ζ(3,3,3) + 6*ζ(4,1,4) + 3*ζ(4,2,3) + ζ(4,3,2)

    TESTS::

        sage: A = QQ['u']
        sage: u = A.gen()
        sage: M = Multizetas(A)
        sage: (u*M((2,))+M((3,)))*M((2,))
        4*u*ζ(1,3) + 6*ζ(1,4) + 2*u*ζ(2,2) + 3*ζ(2,3) + ζ(3,2)
    """
    def __init__(self, R):
        """
        TESTS::

            sage: M = Multizetas(QQ)
            sage: TestSuite(M).run()  # not tested
            sage: M.category()
            Category of commutative no zero divisors graded algebras
            with basis over Rational Field
        """
        if R not in Rings():
            raise TypeError("argument R must be a ring")
        cat = GradedAlgebrasWithBasis(R).Commutative()
        if R in Domains():
            cat = cat & Domains()
        CombinatorialFreeModule.__init__(self, R, Words(NN, infinite=False),
                                         prefix="Z",
                                         category=cat)

    def _repr_(self):
        r"""
        Return a string representation of the algebra.

        EXAMPLES::

            sage: M = Multizetas(QQ); M
            Algebra of motivic multiple zeta values indexed by compositions over Rational Field
        """
        txt = "Algebra of motivic multiple zeta values indexed by compositions over {}"
        return txt.format(self.base_ring())

    def _repr_term(self, m):
        """
        Return a custom string representation for the monomials.

        EXAMPLES::

             sage: Multizeta(2,3)  # indirect doctest
             ζ(2,3)
        """
        return "ζ(" + ','.join(str(letter) for letter in m) + ")"

    @cached_method
    def one_basis(self):
        r"""
        Return the index of the unit for the algebra.

        This is the empty word.

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M.one_basis()
            word:
        """
        return self.basis().keys()([])

    def some_elements(self):
        r"""
        Return some elements of the algebra.

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M.some_elements()
            (ζ(), ζ(2), ζ(3), ζ(4), ζ(1,2))
        """
        return self([]), self([2]), self([3]), self([4]), self((1, 2))

    def product_on_basis(self, w1, w2):
        r"""
        Compute the product of two monomials.

        This is done by converting to iterated integrals and
        using the shuffle product.

        INPUT:

        - ``w1``, ``w2`` -- compositions

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M.product_on_basis([2],[2])
            4*ζ(1,3) + 2*ζ(2,2)
            sage: x = M((2,))
            sage: x*x
            4*ζ(1,3) + 2*ζ(2,2)
        """
        if not w1:
            return self(w2)
        if not w2:
            return self(w1)
        p1 = self.iterated_on_basis(w1)
        p2 = self.iterated_on_basis(w2)
        p1p2 = p1 * p2
        MZV_it = p1p2.parent()
        return MZV_it.composition(p1p2)

    def half_product(self, w1, w2):
        r"""
        Compute half of the product of two elements.

        This comes from half of the shuffle product.

        .. WARNING:: This is not a motivic operation.

        INPUT:

        - ``w1``, ``w2`` -- elements

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M.half_product(M([2]),M([2]))
            2*ζ(1,3) + ζ(2,2)

        TESTS:

            sage: M.half_product(M.one(), M([2]))
            Traceback (most recent call last):
            ...
            ValueError: not defined on the unit
        """
        empty = self.one_basis()
        if w1.coefficient(empty) or w2.coefficient(empty):
            raise ValueError('not defined on the unit')
        p1 = self.iterated(w1)
        p2 = self.iterated(w2)
        MZV_it = p1.parent()
        p1p2 = MZV_it.half_product(p1, p2)
        return MZV_it.composition(p1p2)

    @lazy_attribute
    def iterated(self):
        """
        Convert to the algebra of iterated integrals.

        This is also available as a method of elements.

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: x = M((3,2))
            sage: M.iterated(3*x)
            3*I(10010)
            sage: x = M((2,3,2))
            sage: M.iterated(4*x)
            -4*I(1010010)
        """
        cod = Multizetas_iterated(self.base_ring())
        return self.module_morphism(self.iterated_on_basis, codomain=cod)

    def iterated_on_basis(self, w):
        """
        Convert to the algebra of iterated integrals.

        Beware that this conversion involves signs in our chosen convention.

        INPUT:

        - ``w`` -- a word

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: x = M.basis().keys()((3,2))
            sage: M.iterated_on_basis(x)
            I(10010)
            sage: x = M.basis().keys()((2,3,2))
            sage: M.iterated_on_basis(x)
            -I(1010010)
        """
        codomain = Multizetas_iterated(self.base_ring())
        return (-1)**len(w) * codomain(composition_to_iterated(w))

    def degree_on_basis(self, w):
        """
        Return the degree of the monomial ``w``.

        This is the sum of terms in ``w``.

        INPUT:

        - ``w`` -- a composition

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: x = (2,3)
            sage: M.degree_on_basis(x)  # indirect doctest
            5
        """
        return ZZ(sum(w))

    @lazy_attribute
    def phi(self):
        r"""
        Return the morphism ``phi``.

        This sends multiple zeta values to the algebra :func:`F_ring`,
        which is a shuffle algebra in odd generators `f_3,f_5,f_7,\dots`
        over the polynomial ring in one variable `f_2`.

        This is a ring isomorphism, that depends on the choice of a
        multiplicative basis for the ring of motivic multiple zeta
        values. Here we use one specific hardcoded basis.

        For the precise definition of ``phi`` by induction, see [Brown2012]_.

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: m = Multizeta(2,2) + 2*Multizeta(1,3); m
            2*ζ(1,3) + ζ(2,2)
            sage: M.phi(m)
            1/2*f2^2*Z[]

            sage: Z = Multizeta
            sage: B5 = [3*Z(1,4) + 2*Z(2,3) + Z(3,2), 3*Z(1,4) + Z(2,3)]
            sage: [M.phi(b) for b in B5]
            [f2*Z[f3] - 1/2*Z[f5], 1/2*Z[f5]]
        """
        M_it = Multizetas_iterated(self.base_ring())
        return M_it.phi * self.iterated

    def _element_constructor_(self, x):
        r"""
        Convert ``x`` into ``self``.

        INPUT

        - ``x`` -- either a list, tuple, word or a multiple zeta value

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M(Word((2,3)))
            ζ(2,3)
            sage: M(Word([2,3]))
            ζ(2,3)
            sage: x = M((2,3)); x
            ζ(2,3)
            sage: M(x) == x
            True
        """
        if isinstance(x, (FiniteWord_class, tuple, list)):
            if x:
                assert all(letter >= 1 for letter in x), 'bad letter'
                assert x[-1] >= 2, 'bad last letter'
            W = self.basis().keys()
            return self.monomial(W(x))

        P = x.parent()
        if isinstance(P, Multizetas):
            if P is self:
                return x
            if P is not self.base_ring():
                return self.element_class(self, x.monomial_coefficients())
        elif isinstance(P, Multizetas_iterated):
            return x.composition()

        R = self.base_ring()
        # coercion via base ring
        x = R(x)
        if x == 0:
            return self.element_class(self, {})
        return self.from_base_ring_from_one_basis(x)

    def algebra_generators(self, n):
        """
        Return a set of multiplicative generators in weight ``n``.

        This is obtained from hardcoded data, available only up to weight 17.

        INPUT:

        - ``n`` -- an integer

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M.algebra_generators(5)
            [ζ(5)]
            sage: M.algebra_generators(8)
            [ζ(3,5)]
        """
        return [self(b) for b in B_data[n]]

    def basis_data(self, basering, n):
        """
        Return an iterator for a basis in weight ``n``.

        This is obtained from hardcoded data, available only up to weight 17.

        INPUT:

        - ``n`` -- an integer

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: list(M.basis_data(QQ, 4))
            [4*ζ(1,3) + 2*ζ(2,2)]
        """
        basis_MZV = extend_multiplicative_basis(B_data, n)
        return (prod(self(compo) for compo in term) for term in basis_MZV)

    def basis_brown(self, n):
        r"""
        Return a basis of the algebra of multiple zeta values in weight ``n``.

        It was proved by Francis Brown that this is a basis of motivic
        multiple zeta values.

        This is made of all `\zeta(n_1, ..., n_r)` with parts in {2,3}.

        INPUT:

        - ``n`` -- an integer

        EXAMPLES::

            sage: M = Multizetas(QQ)
            sage: M.basis_brown(3)
            [ζ(3)]
            sage: M.basis_brown(4)
            [ζ(2,2)]
            sage: M.basis_brown(5)
            [ζ(3,2), ζ(2,3)]
            sage: M.basis_brown(6)
            [ζ(3,3), ζ(2,2,2)]
        """
        return [self(tuple(c))
                for c in IntegerVectors(n, min_part=2, max_part=3)]

    class Element(CombinatorialFreeModule.Element):
        def iterated(self):
            """
            Convert to the algebra of iterated integrals.

            Beware that this conversion involves signs.

            EXAMPLES::

                sage: M = Multizetas(QQ)
                sage: x = M((2,3,4))
                sage: x.iterated()
                -I(101001000)
            """
            return self.parent().iterated(self)

        def single_valued(self):
            """
            Return the single valued version of ``self``.

            EXAMPLES::

                sage: M = Multizetas(QQ)
                sage: x = M((2,))
                sage: x.single_valued()
                0
                sage: x = M((3,))
                sage: x.single_valued()
                2*ζ(3)
                sage: x = M((5,))
                sage: x.single_valued()
                2*ζ(5)
                sage: x = M((2,3))
                sage: x.single_valued()
                -11*ζ(5)
            """
            phi_im = self.phi()
            zin = phi_im.parent()
            BR2 = zin.base_ring()
            sv = zin.sum_of_terms((w, BR2(cf(0)))
                                  for (a, b), cf in phi_im.coproduct()
                                  for w in a.shuffle(b))
            return rho_inverse(sv)

        def simplify(self):
            """
            Gather terms using the duality relations.

            This can help to lower the number of monomials.

            EXAMPLES::

                sage: M = Multizetas(QQ)
                sage: z = 3*M((3,)) + 5*M((1,2))
                sage: z.simplify()
                8*ζ(3)
            """
            return self.iterated().simplify().composition()

        def __eq__(self, other):
            """
            Test for equality.

            This means equality as motivic multiple zeta value, computed
            using the morphism ``phi``.

            EXAMPLES::

                sage: M = Multizeta
                sage: 4*M(1,3) == M(4)
                True
                sage: our_pi2 = 6*M(2)
                sage: Multizeta(2,2,2) == our_pi2**3 / 7.factorial()
                True
            """
            return self.iterated().phi() == other.iterated().phi()

        def __ne__(self, other):
            """
            Test for non-equality.

            This means non-equality as motivic multiple zeta value, computed
            using the morphism ``phi``.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizeta
                sage: M(2,2,2) != M(6)
                True
            """
            return not (self == other)

        def phi(self):
            """
            Return the image of ``self`` by the morphism ``phi``.

            This sends multiple zeta values to the algebra :func:`F_ring`.

            EXAMPLES::

                sage: M = Multizetas(QQ)
                sage: M((1,2)).phi()
                Z[f3]

            TESTS::

                sage: A = QQ['u']
                sage: u = A.gen()
                sage: M = Multizetas(A)
                sage: tst = u*M((1,2))+M((3,))
                sage: tst.phi()
                (u+1)*Z[f3]
            """
            return self.parent().phi(self)

        def phi_as_vector(self):
            """
            Return the image of ``self`` by the morphism ``phi`` as a vector.

            The morphism ``phi`` sends multiple zeta values to the algebra
            :func:`F_ring`. Then the image is expressed as a vector in
            a fixed basis of one graded component of this algebra.

            This is only defined for homogeneous elements.

            EXAMPLES::

                sage: M = Multizetas(QQ)
                sage: M((3,2)).phi_as_vector()
                (9/2, -2)

            TESTS::

                sage: (M((4,))+M((1,2))).phi_as_vector()
                Traceback (most recent call last):
                ...
                ValueError: only defined for homogeneous elements
            """
            if not self.is_homogeneous():
                raise ValueError('only defined for homogeneous elements')
            return f_to_vector(self.parent().phi(self))

        def _numerical_approx_pari(self):
            r"""
            The numerical values of individual multiple zeta are obtained via
            the class :class:`MultizetaValues` that performs some caching.

            TESTS::

                sage: M = Multizetas(QQ)
                sage: a = M((3,2)) - 2*M((7,))
                sage: a._numerical_approx_pari()
                -1.30513235721327
                sage: type(a._numerical_approx_pari())
                <class 'cypari2.gen.Gen'>
            """
            return sum(cf * Values.pari_eval(tuple(w)) for w, cf in self.monomial_coefficients().items())

        def numerical_approx(self, prec=None, digits=None, algorithm=None):
            """
            Return a numerical value for this element.

            EXAMPLES::

                sage: M = Multizetas(QQ)
                sage: M(Word((3,2))).n()  # indirect doctest
                0.711566197550572
                sage: parent(M(Word((3,2))).n())
                Real Field with 53 bits of precision

                sage: (M((3,)) * M((2,))).n(prec=80)
                1.9773043502972961181971
                sage: M((1,2)).n(70)
                1.2020569031595942854

                sage: M((3,)).n(digits=10)
                1.202056903

            If you need plan to use intensively numerical approximation at high precision,
            you might want to add more values and/or accuracy to the cache::

                sage: from sage.modular.multiple_zeta import MultizetaValues
                sage: M = MultizetaValues()
                sage: M.update(max_weight=9, prec=2048)
                sage: M
                Cached multiple zeta values at precision 2048 up to weight 9
                sage: M.reset()  # restore precision for the other doctests
            """
            if prec is None:
                if digits:
                    from sage.arith.numerical_approx import digits_to_bits
                    prec = digits_to_bits(digits)
                else:
                    prec = 53
            if algorithm is not None:
                raise ValueError("unknown algorithm")
            if prec < Values.prec:
                s = sum(cf * Values(tuple(w)) for w, cf in self.monomial_coefficients().items())
                return s.n(prec=prec)
            else:
                return sum(cf * Values(tuple(w), prec=prec) for w, cf in self.monomial_coefficients().items())


class Multizetas_iterated(CombinatorialFreeModule):
    r"""
    Secondary class for the algebra of multiple zeta values.

    This is used to represent multiple zeta values as iterated integrals
    of the differential forms `\omega_0 = \dt/t`and `\omega_1 = \dt/(t-1)`.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import Multizetas_iterated
        sage: M = Multizetas_iterated(QQ); M
        Algebra of motivic multiple zeta values as convergent iterated
        integrals over Rational Field
        sage: M((1,0))
        I(10)
        sage: M((1,0))**2
        4*I(1100) + 2*I(1010)
        sage: M((1,0))*M((1,0,0))
        6*I(11000) + 3*I(10100) + I(10010)
    """
    def __init__(self, R):
        """
        TESTS::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: TestSuite(M).run()  # not tested
            sage: M.category()
            Category of commutative no zero divisors graded algebras
            with basis over Rational Field
        """
        if R not in Rings():
            raise TypeError("argument R must be a ring")
        cat = GradedAlgebrasWithBasis(R).Commutative()
        if R in Domains():
            cat = cat & Domains()
        CombinatorialFreeModule.__init__(self, R, Words10, prefix="I",
                                         category=cat)

    def _repr_(self):
        """
        Return a string representation for the ring.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ); M
            Algebra of motivic multiple zeta values as convergent iterated integrals over Rational Field
        """
        return "Algebra of motivic multiple zeta values as convergent iterated integrals over {}".format(self.base_ring())

    def _repr_term(self, m):
        """
        Return a custom string representation for the monomials.

        EXAMPLES::

            sage: Multizeta(1,0,1,0)  # indirect doctest
            I(1010)
        """
        return "I(" + ''.join(str(letter) for letter in m) + ")"

    @cached_method
    def one_basis(self):
        r"""
        Return the index of the unit for the algebra.

        This is the empty word.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: M.one_basis()
            word:
        """
        return self.basis().keys()([])

    def product_on_basis(self, w1, w2):
        r"""
        Compute the product of two monomials.

        This is the shuffle product.

        INPUT:

        - ``w1``, ``w2`` -- words in 0 and 1

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = Word([1,0])
            sage: M.product_on_basis(x,x)
            2*I(1010) + 4*I(1100)
            sage: y = Word([1,1,0])
            sage: M.product_on_basis(y,x)
            I(10110) + 3*I(11010) + 6*I(11100)
        """
        return sum(self.basis()[u] for u in w1.shuffle(w2))

    def half_product_on_basis(self, w1, w2):
        r"""
        Compute half of the product of two monomials.

        This is half of the shuffle product.

        .. WARNING:: This is not a motivic operation.

        INPUT:

        - ``w1``, ``w2`` -- monomials

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = Word([1,0])
            sage: M.half_product_on_basis(x,x)
            2*I(1100) + I(1010)
        """
        assert w1
        W = self.basis().keys()
        u1 = W([w1[0]])
        r1 = w1[1:]
        return sum(self.basis()[u1 + u] for u in r1.shuffle(w2))

    @lazy_attribute
    def half_product(self):
        r"""
        Compute half of the product of two elements.

        This is half of the shuffle product.

        .. WARNING:: This is not a motivic operation.

        INPUT:

        - ``w1``, ``w2`` -- elements

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = M(Word([1,0]))
            sage: M.half_product(x,x)
            2*I(1100) + I(1010)
        """
        half = self.half_product_on_basis
        return self._module_morphism(self._module_morphism(half, position=0,
                                                           codomain=self),
                                     position=1)

    def coproduct_on_basis(self, w):
        """
        Return the motivic coproduct of a monomial.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: M.coproduct_on_basis([1,0])
            I() # I(10) + I(10) # I()

            sage: M.coproduct_on_basis((1,0,1,0))
            I() # I(1010) + 3*I(10) # I(10) + I(1010) # I()
        """
        seq = [0] + list(w) + [1]
        terms = coproduct_iterator(([0], seq))
        M_all = All_iterated(self.base_ring())

        def split_word(indices):
            L = self.one()
            for i in range(len(indices) - 1):
                w = Word(seq[indices[i]:indices[i + 1] + 1])
                if len(w) >= 4:
                    value = M_all(w)
                    L *= value.regularise()
            return L

        resu = self.tensor_square().zero()
        for indices in terms:
            resu += split_word(indices).tensor(
                M_all(Word(seq[i] for i in indices)).regularise())
        return resu

    @lazy_attribute
    def coproduct(self):
        """
        Return the motivic coproduct of an element.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: a = 3*Multizeta(1,4) + Multizeta(2,3)
            sage: M.coproduct(a.iterated())
            3*I() # I(11000) + I() # I(10100) + 3*I(11000) # I()
            - I(10) # I(100) + I(10100) # I()
        """
        cop = self.coproduct_on_basis
        return self._module_morphism(cop, codomain=self.tensor_square())

    @lazy_attribute
    def composition(self):
        """
        Convert to the algebra of multiple zeta values of composition style.

        This means the algebra :class:`Multizetas`.

        This is also available as a method of elements.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = M((1,0))
            sage: M.composition(2*x)
            -2*ζ(2)
            sage: x = M((1,0,1,0,0))
            sage: M.composition(x)
            ζ(2,3)
        """
        cod = Multizetas(self.base_ring())
        return self.module_morphism(self.composition_on_basis, codomain=cod)

    def composition_on_basis(self, w, basering=None):
        """
        Convert to the algebra of multiple zeta values of composition style.

        INPUT:

        - ``basering`` -- optional choice of the coefficient ring

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: M.composition_on_basis(x)
            ζ(2,3)
            sage: x = Word((1,0,1,0,0,1,0))
            sage: M.composition_on_basis(x)
            -ζ(2,3,2)
        """
        if basering is None:
            basering = self.base_ring()
        codomain = Multizetas(basering)
        return (-1)**w.count(1) * codomain(iterated_to_composition(w))

    def dual_on_basis(self, w):
        """
        Return the order of the word and exchange letters 0 and 1.

        This is an involution.

        INPUT:

        - ``w`` -- a word in 0 and 1

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: M.dual_on_basis(x)
            -I(11010)
        """
        rev = [1 - x for x in reversed(w)]
        return (-1)**len(w) * self(self.basis().keys()(rev))

    def degree_on_basis(self, w):
        """
        Return the degree of the monomial ``w``.

        This is the length of the word.

        INPUT:

        - ``w`` -- a word in 0 and 1

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: M.degree_on_basis(x)
            5
        """
        return ZZ(len(w))

    def D_on_basis(self, k, w):
        """
        Return the action of the operator `D_k` on the monomial ``w``.

        This is one main tool in the procedure that allows
        to map the algebra of multiple zeta values to
        the F Ring.

        INPUT:

        - ``k`` -- an odd integer, at least 3

        - ``w`` -- a word in 0 and 1

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: M.D_on_basis(3,(1,1,1,0,0))
            I(110) # I(10) + 2*I(100) # I(10)

            sage: M.D_on_basis(3,(1,0,1,0,0))
            3*I(100) # I(10)
            sage: M.D_on_basis(5,(1,0,0,0,1,0,0,1,0,0))
            10*I(10000) # I(10100)
        """
        Im = All_iterated(self.base_ring())
        MZV_MZV = self.tensor_square()
        N = len(w)
        it = [0] + list(w) + [1]
        coprod = MZV_MZV.zero()
        for p in range(N + 1 - k):
            left = Im(it[p: p + k + 2])
            right = Im(it[:p + 1] + it[p + k + 1:])
            if left and right:
                coprod += left.regularise().tensor(right.regularise())
        return coprod

    @cached_method
    def phi_extended(self, w):
        r"""
        Return the image of the monomial ``w`` by the morphism ``phi``.

        INPUT:

        - ``w`` -- a word in 0 and 1

        OUTPUT:

        an element in the algebra :func:`F_ring`

        The coefficients are in the base ring.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: M.phi_extended((1,0))
            -f2*Z[]
            sage: M.phi_extended((1,0,0))
            -Z[f3]
            sage: M.phi_extended((1,1,0))
            Z[f3]
            sage: M.phi_extended((1,0,1,0,0))
            3*f2*Z[f3] - 11/2*Z[f5]

        More complicated examples::

            sage: from sage.modular.multiple_zeta import composition_to_iterated
            sage: M.phi_extended(composition_to_iterated((4,3)))
            2/5*f2^2*Z[f3] + 10*f2*Z[f5] - 18*Z[f7]

            sage: M.phi_extended(composition_to_iterated((3,4)))
            -10*f2*Z[f5] + 17*Z[f7]

            sage: M.phi_extended(composition_to_iterated((4,2)))
            10/21*f2^3*Z[] - 2*Z[f3,f3]
            sage: M.phi_extended(composition_to_iterated((3,5)))
            -5*Z[f5,f3]
            sage: M.phi_extended(composition_to_iterated((3,7)))
            -6*Z[f5,f5] - 14*Z[f7,f3]

            sage: M.phi_extended(composition_to_iterated((3,3,2)))
            -793/875*f2^4*Z[] - 4*f2*Z[f3,f3] + 9*Z[f3,f5] - 9/2*Z[f5,f3]

        TESTS::

           sage: M.phi_extended(tuple([]))
           Z[]
        """
        # this is now hardcoded
        # prec = 1024
        f = F_ring_generator
        if not w:
            F = F_ring(self.base_ring())
            empty = F.indices()([])
            return F.monomial(empty)
        N = len(w)
        compo = tuple(iterated_to_composition(w))
        BRf2 = PolynomialRing(self.base_ring(), 'f2')
        if compo in B_data[N]:
            # do not forget the sign
            result_QQ = (-1)**len(compo) * phi_on_multiplicative_basis(compo)
            return result_QQ.base_extend(BRf2)
        u = compute_u_on_basis(w)
        rho_inverse_u = rho_inverse(u)
        xi = self.composition_on_basis(w, QQ)
        c_xi = (xi - rho_inverse_u)._numerical_approx_pari()
        c_xi /= Multizeta(N)._numerical_approx_pari()
        c_xi = c_xi.bestappr().sage()  # in QQ
        result_QQ = u + c_xi * f(N)
        return result_QQ.base_extend(BRf2)

    @lazy_attribute
    def phi(self):
        """
        Return the morphism ``phi``.

        This sends multiple zeta values to the algebra :func:`F_ring`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: m = Multizeta(1,0,1,0) + 2*Multizeta(1,1,0,0); m
            2*I(1100) + I(1010)
            sage: M.phi(m)
            1/2*f2^2*Z[]

            sage: Z = Multizeta
            sage: B5 = [3*Z(1,4) + 2*Z(2,3) + Z(3,2), 3*Z(1,4) + Z(2,3)]
            sage: [M.phi(b.iterated()) for b in B5]
            [f2*Z[f3] - 1/2*Z[f5], 1/2*Z[f5]]

            sage: B6 = [6*Z(1,5) + 3*Z(2,4) + Z(3,3),
            ....:  6*Z(1,1,4) + 4*Z(1,2,3) + 2*Z(1,3,2) + 2*Z(2,1,3) + Z(2,2,2)]
            sage: [M.phi(b.iterated()) for b in B6]
            [Z[f3,f3], 1/6*f2^3*Z[]]
        """
        cod = F_ring(self.base_ring())
        return self.module_morphism(self.phi_extended, codomain=cod)

    def _element_constructor_(self, x):
        r"""
        Convert ``x`` into ``self``.

        INPUT

        - ``x`` -- either a list, tuple, word or a multiple zeta value

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import Multizetas_iterated
            sage: M = Multizetas_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: M(x)
            I(10100)
            sage: y = M((1,1,0,0)); y
            I(1100)
            sage: y == M(y)
            True
        """
        if isinstance(x, (str, (FiniteWord_class, tuple, list))):
            if x:
                assert all(letter in (0, 1) for letter in x), 'bad letter'
                assert x[0] == 1, 'bad first letter, should be 1'
                assert x[-1] == 0, 'bad last letter, should be 0'
            W = self.basis().keys()
            return self.monomial(W(x))

        P = x.parent()
        if isinstance(P, Multizetas_iterated):
            if P is self:
                return x
            if P is not self.base_ring():
                return self.element_class(self, x.monomial_coefficients())
        elif isinstance(P, Multizetas):
            return x.iterated()

        R = self.base_ring()
        # coercion via base ring
        x = R(x)
        if x == 0:
            return self.element_class(self, {})
        else:
            return self.from_base_ring_from_one_basis(x)

    class Element(CombinatorialFreeModule.Element):
        def simplify(self):
            """
            Gather terms using the duality relations.

            This can help to lower the number of monomials.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizetas_iterated(QQ)
                sage: z = 4*M((1,0,0)) + 3*M((1,1,0))
                sage: z.simplify()
                I(100)
            """
            summing = self.parent().sum_of_terms
            return summing(minimize_term(w, cf)
                           for w, cf in self.monomial_coefficients().items())

        def composition(self):
            """
            Convert to the algebra of multiple zeta values of composition style.

            This means the algebra :class:`Multizetas`.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizetas_iterated(QQ)
                sage: x = M((1,0,1,0))
                sage: x.composition()
                ζ(2,2)
                sage: x = M((1,0,1,0,0))
                sage: x.composition()
                ζ(2,3)
                sage: x = M((1,0,1,0,0,1,0))
                sage: x.composition()
                -ζ(2,3,2)
            """
            return self.parent().composition(self)

        def numerical_approx(self, prec=None, digits=None, algorithm=None):
            """
            Return a numerical approximation as a sage real.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizetas_iterated(QQ)
                sage: x = M((1,0,1,0))
                sage: y = M((1, 0, 0))
                sage: (3*x+y).n()  # indirect doctest
                1.23317037269047
            """
            return self.composition().numerical_approx(prec=prec, digits=digits, algorithm=algorithm)

        def phi(self):
            """
            Return the image of ``self`` by the morphism ``phi``.

            This sends multiple zeta values to the algebra :func:`F_ring`.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizetas_iterated(QQ)
                sage: M((1,1,0)).phi()
                Z[f3]
            """
            return self.parent().phi(self)

        def __eq__(self, other):
            """
            Test for equality.

            This means equality as motivic multiple zeta value, computed
            using the morphism ``phi``.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizetas_iterated(QQ)
                sage: M((1,1,0)) == -M((1,0,0))
                True

                sage: M = Multizetas(QQ)
                sage: a = 28*M((3,9))+150*M((5,7))+168*M((7,5))
                sage: b = 5197/691*M((12,))
                sage: a.iterated() == b.iterated() # not tested, long time 20s
                True
            """
            return self.phi() == other.phi()

        def __ne__(self, other):
            """
            Test for non-equality.

            This means non-equality as motivic multiple zeta value, computed
            using the morphism ``phi``.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import Multizetas_iterated
                sage: M = Multizetas_iterated(QQ)
                sage: M((1,0)) == M((1,0,0))
                False
            """
            return not (self == other)


class All_iterated(CombinatorialFreeModule):
    r"""
    Auxiliary class for multiple zeta value as generalized iterated integrals.

    This is used to represent multiple zeta values as possibly
    divergent iterated integrals
    of the differential forms `\omega_0 = \dt/t`and `\omega_1 = \dt/(t-1)`.

    This means that the elements are symbols
    `I(a_0 ; a_1,a_2,...a_m ; a_{n+1})`
    where all arguments, including the starting and ending points
    can be 0 or 1.

    This comes with a "regularise" method mapping
    to :class:`Multizeta_iterated`.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import All_iterated
        sage: M = All_iterated(QQ); M
        Space of motivic multiple zeta values as general iterated integrals
        over Rational Field
        sage: M((0,1,0,1))
        I(0;10;1)
        sage: x = M((1,1,0,0)); x
        I(1;10;0)
        sage: x.regularise()
        -I(10)
    """
    def __init__(self, R):
        """
        TESTS::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: TestSuite(M).run()  # not tested
        """
        if R not in Rings():
            raise TypeError("argument R must be a ring")
        CombinatorialFreeModule.__init__(self, R, Words10, prefix="I")

    def _repr_(self):
        """
        Return a string representation of the module.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ); M
            Space of motivic multiple zeta values as general iterated integrals over Rational Field
        """
        txt = "Space of motivic multiple zeta values as general iterated integrals over {}"
        return txt.format(self.base_ring())

    def _repr_term(self, m):
        """
        Return a custom string representation for the monomials.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: M(x)  # indirect doctest
            I(1;010;0)
        """
        start = str(m[0])
        end = str(m[-1])
        mid = ''.join(str(letter) for letter in m[1:-1])
        return "I(" + start + ";" + mid + ";" + end + ")"

    def _element_constructor_(self, x):
        r"""
        Convert ``x`` into ``self``.

        INPUT

        - ``x`` -- either a list, tuple, word

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: y = M((1,1,0,0)); y
            I(1;10;0)
            sage: y == M(y)
            True
        """
        if isinstance(x, (str, (FiniteWord_class, tuple, list))):
            if x:
                assert all(letter in (0, 1) for letter in x), 'bad letter'
                # assert len(x) >= 4, 'word too short'
            W = self.basis().keys()
            mot = W(x)
            # conditions R1 de F. Brown
            if mot[0] == mot[-1] or (len(x) >= 4 and
                                     all(x == mot[1] for x in mot[2:-1])):
                return self.zero()
            return self.monomial(mot)

    def dual_on_basis(self, w):
        """
        Reverse the word and exchange the letters 0 and 1.

        This is the operation R4 in [Brown2012]_.

        This should be used only when `a_0 = 0` and `a_{n+1} = 1`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((0,0,1,0,1))
            sage: M.dual_on_basis(x)
            I(0;010;1)
            sage: x = Word((0,1,0,1,1))
            sage: M.dual_on_basis(x)
            -I(0;010;1)
        """
        if w[-2] == 0:
            return self(w)
        rev = [1 - x for x in reversed(w)]
        return (-1)**len(w) * self(self.basis().keys()(rev))

    @lazy_attribute
    def dual(self):
        """
        Reverse words and exchange the letters 0 and 1.

        This is the operation R4 in [Brown2012]_.

        This should be used only when `a_0 = 0` and `a_{n+1} = 1`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((0,0,1,1,1))
            sage: y = Word((0,0,1,0,1))
            sage: M.dual(M(x)+5*M(y))
            5*I(0;010;1) - I(0;001;1)
        """
        return self.module_morphism(self.dual_on_basis, codomain=self)

    def reversal_on_basis(self, w):
        """
        Reverse the word if necessary.

        This is the operation R3 in [Brown2012]_.

        This reverses the word only if `a_0 = 0` and `a_{n+1} = 1`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: M.reversal_on_basis(x)
            -I(0;010;1)
            sage: x = Word((0,0,1,1,1))
            sage: M.reversal_on_basis(x)
            I(0;011;1)
        """
        if w[0] == 0 and w[-1] == 1:
            return self(w)
        W = self.basis().keys()
        return (-1)**len(w) * self.monomial(W(list(reversed(w))))

    @lazy_attribute
    def reversal(self):
        """
        Reverse words if necessary.

        This is the operation R3 in [Brown2012]_.

        This reverses the word only if `a_0 = 0` and `a_{n+1} = 1`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((1,0,1,0,0))
            sage: y = Word((0,0,1,1,1))
            sage: M.reversal(M(x)+2*M(y))
            2*I(0;011;1) - I(0;010;1)
        """
        return self.module_morphism(self.reversal_on_basis, codomain=self)

    def expand_on_basis(self, w):
        """
        Perform an expansion as a linear combination.

        This is the operation R2 in [Brown2012]_.

        This should be used only when `a_0 = 0` and `a_{n+1} = 1`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((0,0,1,0,1))
            sage: M.expand_on_basis(x)
            -2*I(0;100;1)

            sage: x = Word((0,0,0,1,0,1,0,0,1))
            sage: M.expand_on_basis(x)
            6*I(0;1010000;1) + 6*I(0;1001000;1) + 3*I(0;1000100;1)

            sage: x = Word((0,1,1,0,1))
            sage: M.expand_on_basis(x)
            I(0;110;1)
        """
        if w[1] == 1:
            return self(w)

        mot = w[1:-1]
        n_zeros = []
        k = 0
        for x in mot:
            if x == 0:
                k += 1
            else:
                n_zeros.append(k)
                k = 1
        n_zeros.append(k)
        k = n_zeros[0]
        n_zeros = n_zeros[1:]
        r = len(n_zeros)

        resu = self.zero()
        for idx in IntegerVectors(k, r):
            coeff = ZZ.prod(ZZ(nj + ij - 1).binomial(ij)
                            for nj, ij in zip(n_zeros, idx))
            indice = [0]
            for nj, ij in zip(n_zeros, idx):
                indice += [1] + [0] * (nj + ij - 1)
            resu += coeff * self(indice + [1])
        return (-1)**k * resu  # attention au signe

    @lazy_attribute
    def expand(self):
        """
        Perform an expansion as a linear combination.

        This is the operation R2 in [Brown2012]_.

        This should be used only when `a_0 = 0` and `a_{n+1} = 1`.

        EXAMPLES::

            sage: from sage.modular.multiple_zeta import All_iterated
            sage: M = All_iterated(QQ)
            sage: x = Word((0,0,1,0,1))
            sage: y = Word((0,0,1,1,1))
            sage: M.expand(M(x)+2*M(y))
            -2*I(0;110;1) - 2*I(0;101;1) - 2*I(0;100;1)
            sage: M.expand(M([0,1,1,0,1]))
            I(0;110;1)
            sage: M.expand(M([0,1,0,0,1]))
            I(0;100;1)
        """
        return self.module_morphism(self.expand_on_basis, codomain=self)

    class Element(CombinatorialFreeModule.Element):
        def conversion(self):
            """
            Conversion to the :class:`Multizeta_iterated`.

            This assumed that the element has been prepared.

            Not to be used directly.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import All_iterated
                sage: M = All_iterated(QQ)
                sage: x = Word((0,1,0,0,1))
                sage: y = M(x).conversion(); y
                I(100)
                sage: y.parent()
                Algebra of motivic multiple zeta values as convergent iterated
                integrals over Rational Field
            """
            M = Multizetas_iterated(self.parent().base_ring())
            return sum(cf * M.monomial(w[1:-1]) for w, cf in self)

        def regularise(self):
            """
            Conversion to the :class:`Multizeta_iterated`.

            This is the regularisation procedure, done in several steps.

            EXAMPLES::

                sage: from sage.modular.multiple_zeta import All_iterated
                sage: M = All_iterated(QQ)
                sage: x = Word((0,0,1,0,1))
                sage: M(x).regularise()
                -2*I(100)
                sage: x = Word((0,1,1,0,1))
                sage: M(x).regularise()
                I(110)

                sage: x = Word((1,0,1,0,0))
                sage: M(x).regularise()
                2*I(100)
            """
            P = self.parent()
            step1 = P.reversal(self)  # R3
            step2 = P.expand(step1)   # R2
            step3 = P.dual(step2)     # R4
            step4 = P.expand(step3)    # R2
            return step4.conversion()  # dans Multizeta_iterated


# **************** procedures after F. Brown ************


def F_ring(basering, N=18):
    r"""
    Return the free Zinbiel algebra on many generators `f_3,f_5,\dots`
    over the polynomial ring with generator `f_2`.

    For the moment, only with a finite number of variables.

    INPUT:

    - ``N`` -- an integer (default 18), upper bound for indices of generators

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import F_ring
        sage: F_ring(QQ)
        Free Zinbiel algebra on generators (Z[f3], Z[f5], Z[f7], Z[f9], ...)
        over Univariate Polynomial Ring in f2 over Rational Field
    """
    ring = PolynomialRing(basering, ['f2'])
    return FreeZinbielAlgebra(ring, ['f{}'.format(k)
                                     for k in range(3, N, 2)])


def F_prod(a, b):
    """
    Return the associative and commutative product of ``a`` and ``b``.

    INPUT:

    - ``a``, ``b`` -- two elements of the F ring

    OUTPUT:

    an element of the F ring

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import F_ring_generator, F_prod
        sage: f2 = F_ring_generator(2)
        sage: f3 = F_ring_generator(3)
        sage: F_prod(f2,f2)
        f2^2*Z[]
        sage: F_prod(f2,f3)
        f2*Z[f3]
        sage: F_prod(f3,f3)
        2*Z[f3,f3]
        sage: F_prod(3*f2+5*f3,6*f2+f3)
        18*f2^2*Z[] + 33*f2*Z[f3] + 10*Z[f3,f3]
    """
    F = a.parent()
    empty = F.indices()([])
    one = F.monomial(empty)
    ct_a = a.coefficient(empty)
    ct_b = b.coefficient(empty)
    rem_a = a - ct_a * one
    rem_b = b - ct_b * one
    resu = ct_a * ct_b * one + ct_a * rem_b + ct_b * rem_a
    return resu + rem_a * rem_b + rem_b * rem_a


def F_ring_generator(i):
    r"""
    Return the generator of the F ring over `\QQ`.

    INPUT:

    - ``i`` -- a nonnegative integer

    If ``i`` is odd, this returns a single generator `f_i` of the free
    shuffle algebra.

    Otherwise, it returns an appropriate multiple of a power of `f_2`.

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import F_ring_generator
        sage: [F_ring_generator(i) for i in range(2,8)]
        [f2*Z[], Z[f3], 2/5*f2^2*Z[], Z[f5], 8/35*f2^3*Z[], Z[f7]]
    """
    F = F_ring(QQ)
    one = F.monomial(Word([]))
    f2 = F.base_ring().gen()
    if i == 2:
        return f2 * one
    # now i odd >= 3
    if i % 2:
        return F.monomial(Word(['f{}'.format(i)]))
    i = i // 2
    B = bernoulli(2 * i) * (-1)**(i - 1)
    B *= ZZ(2)**(3 * i - 1) * ZZ(3)**i / ZZ(2 * i).factorial()
    return B * f2**i * one


def coeff_phi(w):
    """
    Return the coefficient of `f_k` in the image by ``phi``.

    INPUT:

    - ``w`` -- a word in 0 and 1 with `k` letters (where `k` is odd)

    OUTPUT:

    a rational number

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import coeff_phi
        sage: coeff_phi(Word([1,0,0]))
        -1
        sage: coeff_phi(Word([1,1,0]))
        1
        sage: coeff_phi(Word([1,1,0,1,0]))
        11/2
        sage: coeff_phi(Word([1,1,0,0,0,1,0]))
        109/16
    """
    if all(x == 0 for x in w[1:]):
        return -1   # beware the sign
    k = len(w)
    assert k % 2
    M = Multizetas_iterated(QQ)
    z = M.phi_extended(w)
    W = z.parent().basis().keys()
    w = W(['f{}'.format(k)])
    return z.coefficient(w).lc()  # in QQ


def phi_on_multiplicative_basis(compo):
    """
    Compute ``phi`` on one single multiple zeta value.

    INPUT:

    - ``compo`` -- a composition (in the hardcoded multiplicative base)

    OUTPUT:

    an element in :func:`F_ring` with rational coefficients

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import phi_on_multiplicative_basis
        sage: phi_on_multiplicative_basis((2,))
        f2*Z[]
        sage: phi_on_multiplicative_basis((3,))
        Z[f3]
    """
    f = F_ring_generator
    F = F_ring(QQ)
    one = F.monomial(Word([]))

    if tuple(compo) == (2,):
        return f(2) * one

    if len(compo) == 1:
        n, = compo
        return f(n)

    return compute_u_on_compo(compo)


def phi_on_basis(L):
    """
    Compute the value of phi on the hardcoded basis.

    INPUT:

    a list of compositions, each composition in the hardcoded basis

    This encodes a product of multiple zeta values.

    OUTPUT:

    an element in :func:`F_ring`

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import phi_on_basis
        sage: phi_on_basis([(3,),(3,)])
        2*Z[f3,f3]
        sage: phi_on_basis([(2,),(2,)])
        f2^2*Z[]
        sage: phi_on_basis([(2,),(3,),(3,)])
        2*f2*Z[f3,f3]
    """
    # beware that the default * is the half-shuffle !
    F = F_ring(QQ)
    resu = F.monomial(Word([]))
    for compo in L:
        resu = F_prod(resu, phi_on_multiplicative_basis(compo))
    return resu


def D_on_compo(k, compo):
    """
    Return the value of the operator `D_k` on a multiple zeta value.

    This is now only used as a place to keep many doctests.

    INPUT:

    - ``k`` -- an odd integer

    - ``compo`` -- a composition

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import D_on_compo
        sage: D_on_compo(3,(2,3))
        3*I(100) # I(10)

        sage: D_on_compo(3,(4,3))
        I(100) # I(1000)
        sage: D_on_compo(5,(4,3))
        10*I(10000) # I(10)

        sage: [D_on_compo(k, [3,5]) for k in (3,5,7)]
        [0, -5*I(10000) # I(100), 0]

        sage: [D_on_compo(k, [3,7]) for k in (3,5,7,9)]
        [0, -6*I(10000) # I(10000), -14*I(1000000) # I(100), 0]

        sage: D_on_compo(3,(4,3,3))
        -I(100) # I(1000100)
        sage: D_on_compo(5,(4,3,3))
        -10*I(10000) # I(10100)
        sage: D_on_compo(7,(4,3,3))
        4*I(1001000) # I(100) + 2*I(1000100) # I(100)

        sage: [D_on_compo(k,(1,3,1,3,1,3)) for k in range(3,10,2)]
        [0, 0, 0, 0]
    """
    it = composition_to_iterated(compo)
    M = Multizetas_iterated(QQ)
    return (-1)**len(compo) * M.D_on_basis(k, it)


def compute_u_on_compo(compo):
    r"""
    Compute the value of the map ``u`` on a multiple zeta value.

    INPUT:

    - ``compo`` -- a composition

    OUTPUT:

    an element of :func:`F_ring` over `\QQ`

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import compute_u_on_compo
        sage: compute_u_on_compo((2,4))
        2*Z[f3,f3]
        sage: compute_u_on_compo((2,3,2))
        -11/2*f2*Z[f5]
        sage: compute_u_on_compo((3,2,3,2))
        11*f2*Z[f3,f5] - 75/4*Z[f3,f7] - 9*f2*Z[f5,f3] + 81/4*Z[f5,f5] + 75/8*Z[f7,f3]
    """
    it = composition_to_iterated(compo)
    return (-1)**len(compo) * compute_u_on_basis(it)


def compute_u_on_basis(w):
    r"""
    Compute the value of ``u`` on a multiple zeta value.

    INPUT:

    - ``w`` -- a word in 0,1

    OUTPUT:

    an element of :func:`F_ring` over `\QQ`

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import compute_u_on_basis
        sage: compute_u_on_basis((1,0,0,0,1,0))
        -2*Z[f3,f3]

        sage: compute_u_on_basis((1,1,1,0,0))
        f2*Z[f3]

        sage: compute_u_on_basis((1,0,0,1,0,0,0,0))
        -5*Z[f5,f3]

        sage: compute_u_on_basis((1,0,1,0,0,1,0))
        11/2*f2*Z[f5]

        sage: compute_u_on_basis((1,0,0,1,0,1,0,0,1,0))
        11*f2*Z[f3,f5] - 75/4*Z[f3,f7] - 9*f2*Z[f5,f3] + 81/4*Z[f5,f5]
        + 75/8*Z[f7,f3]
    """
    M = Multizetas_iterated(QQ)
    F = F_ring(QQ)
    f = F_ring_generator
    N = len(w)
    xi_dict = {}
    for k in range(3, N, 2):
        xi_dict[k] = F.sum(cf * coeff_phi(ww[0]) * M.phi_extended(tuple(ww[1]))
                           for ww, cf in M.D_on_basis(k, w))
    return F.sum(f(k) * xi_dict[k] for k in range(3, N, 2))


def f_to_vector(elt):
    """
    Convert an element of F ring to a vector.

    INPUT:

    an homogeneous element of :func:`F_ring` over some base ring

    OUTPUT:

    a vector with coefficients in the base ring

    .. SEEALSO:: :func:`vector_to_f`

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import F_ring, vector_to_f, f_to_vector
        sage: F = F_ring(QQ)
        sage: f2 = F.base_ring().gen()
        sage: x = f2**4*F.monomial(Word([]))+f2*F.monomial(Word(['f3','f3']))
        sage: f_to_vector(x)
        (0, 0, 1, 1)
        sage: vector_to_f(_,8)
        f2^4*Z[] + f2*Z[f3,f3]

        sage: x = F.monomial(Word(['f11'])); x
        Z[f11]
        sage: f_to_vector(x)
        (1, 0, 0, 0, 0, 0, 0, 0, 0)
    """
    F = elt.parent()
    BR = F.base_ring().base_ring()
    a, b = next(iter(elt))
    N = sum(int(x[1:]) for x in a) + 2 * b.degree()
    W = F.basis().keys()
    return vector(BR, [elt.coefficient(W(b)).lc()
                       for _, b in basis_f_iterator(N)])


def vector_to_f(vec, N):
    """
    Convert back a vector to an element of the F ring.

    INPUT:

    a vector with coefficients in some base ring

    OUTPUT:

    an homogeneous element of :func:`F_ring` over this base ring

    .. SEEALSO:: :func:`f_to_vector`

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import vector_to_f, f_to_vector
        sage: vector_to_f((4,5),6)
        5*f2^3*Z[] + 4*Z[f3,f3]
        sage: f_to_vector(_)
        (4, 5)
    """
    if isinstance(vec, (list, tuple)):
        vec = vector(vec)
    BR = vec.base_ring()
    F = F_ring(BR)
    f2 = F.base_ring().gen()
    basis_F = (f2**k * F.monomial(b)
               for k, b in basis_f_iterator(N))
    return sum(cf * bi for cf, bi in zip(vec, basis_F))


@cached_function
def rho_matrix_inverse(n):
    """
    Return the matrix of the inverse of ``rho``.

    This is the matrix in the chosen bases, namely the hardcoded basis
    of multiple zeta values and the natural basis of the F ring.

    INPUT:

    - ``n`` -- an integer

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import rho_matrix_inverse
        sage: rho_matrix_inverse(3)
        [1]
        sage: rho_matrix_inverse(8)
        [-1/5    0    0    0]
        [ 1/5    1    0    0]
        [   0    0  1/2    0]
        [   0    0    0    1]
    """
    base = extend_multiplicative_basis(B_data, n)
    resu = []
    for b in base:
        phi_b = phi_on_basis(b)
        resu.append(f_to_vector(phi_b))
    dN = len(resu)
    return ~matrix(QQ, dN, dN, resu)


def rho_inverse(elt):
    """
    Return the image by the inverse of ``rho``.

    INPUT:

    - ``elt`` -- an homogeneous element of the F ring

    OUTPUT:

    a linear combination of multiple zeta values

    EXAMPLES::

        sage: from sage.modular.multiple_zeta import F_ring_generator, rho_inverse
        sage: f = F_ring_generator
        sage: rho_inverse(f(3))
        ζ(3)
        sage: rho_inverse(f(9))
        ζ(9)
        sage: rho_inverse(f(5)*f(3))
        -1/5*ζ(3,5)
    """
    pa = elt.parent()
    BR = pa.base_ring().base_ring()
    M_BR = Multizetas(BR)
    if elt == pa.zero():
        return M_BR.zero()

    a, b = next(iter(elt))
    N = sum(int(x[1:]) for x in a) + 2 * b.degree()

    v = f_to_vector(elt)
    w = v * rho_matrix_inverse(N)
    return sum(cf * b for cf, b in zip(w, M_BR.basis_data(BR, N)))
