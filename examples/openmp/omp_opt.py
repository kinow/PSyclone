#!/usr/bin/env python
# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2018, Science and Technology Facilities Council
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
# Authors: Joerg Henrichs, Bureau of Meteorology


from __future__ import print_function, absolute_import

from psyclone.nemo import NemoLoop
from psyclone.core.access_info import VariablesAccessInfo
from psyclone.core.access_type import AccessType
from psyclone.psyGen import Assignment, CodeBlock, IfBlock, Loop
from psyclone.transformations import OMPLoopTrans, OMPParallelTrans


def is_blockable(node):
    '''Returns true if the node (and all included nodes in the subtree)
    can become part of one omp parallel block
    :param node: The node containing the statement(s) to be checked.
    :type node: :py:class:`psyclone.psyGen.Node`
    '''

    # Loops and Assignments can be executed in parallel (if a loop can
    # not be parallelised, we can add a omp serial directive, but it does
    # not prevent a larger omp parallel block from being created.
    # pylint: disable=too-many-return-statements
    if isinstance(node, Assignment):
        return True

    if isinstance(node, NemoLoop):
        if node.loop_type != "lat":
            return False
        # Check if the loop is at least nested:
        nested_loops = node.walk(node.children, Loop)
        return nested_loops != []

    # Likely a function call. This must be outside of an omp block, since
    # the called function itself might be omp parallelised.
    if isinstance(node, CodeBlock):
        return False

    # If blocks can be used, if all parts of the if and else bodies can
    # be within an omp block.
    if isinstance(node, IfBlock):
        # if statements can be used if all their statements are blockable
        for child in node.if_body:
            if not is_blockable(child):
                return False
        # The if body is fine, the whole if statement can be enclosed,
        # if the else body can be blocked as well (or is empty of course)
        for child in node.else_body:
            if not is_blockable(child):
                return False
        return True

    # Anything else - don't allow it to be inside an omp block.
    return False


def collect_loop_blocks(node, blocks=None):
    '''This function collects consecutive loops into one list. The idea is that
    these loops can then (potentially) be parallelised in one omp parallel
    region with individual omp do directives.
    :param node: Subtree to analyse.
    :param blocks:
    '''
    state = "find beginning"
    loops = []
    for child in node.children:
        if state == "find beginning":
            if not is_blockable(child):
                if not isinstance(child, IfBlock):
                    continue
                if_blocks = []
                collect_loop_blocks(child.children[1], if_blocks)
                if if_blocks:
                    blocks += if_blocks
                if child.else_body:
                    collect_loop_blocks(child.children[1], if_blocks)
                    if if_blocks:
                        blocks += if_blocks
                continue

        state = "collecting loops"
        if state == "collecting loops" and \
                not is_blockable(child):
            state = "find beginning"
            if loops:
                blocks.append(loops)
            loops = []
            continue
        loops.append(child)


def is_scalar_parallelisable(var_info):
    '''
    :param var_info:
    :type var_info: :py:class:`psyclone.core.var_info.VariableInfo`
    :return: True if the scalar variable is not a reduction, i.e. it \
        can be parallelised.
    '''

    # Read only scalar variables can be parallelised
    if var_info.is_read_only():
        return (True, "")

    all_accesses = var_info.get_all_accesses()
    # The variable is used only once. Either it is a read-only variable,
    # or it is supposed to store the result from the loop to be used outside
    # of the loop (or it is bad code). Read-only access has already been
    # tested above, so it must be a write access here, which prohibits
    # parallelisation.
    # TODO: should we use lastprivate here?
    if len(all_accesses) == 1:
        return (False, "Variable {0} is only written once"
                .format(var_info.get_var_name()))

    # Now we have at least two accesses. If the first access is a WRITE,
    # then the variable is not used in a reduction. This relies on sorting
    # the accesses by location.
    if all_accesses[0].get_access_type() == AccessType.WRITE:
        return (True, "")

    # Otherwise there is a read first, which would indicate that this loop
    # is a reduction, which is not supported atm.
    return (False, "Variable {0} read first, which indicates a reduction."
            .format(var_info.get_var_name()))


def is_array_parallelisable(loop_variable, var_info):
    '''Tries to determine if the access pattern for a variable
    given in var_info allows parallelisation along the variable
    loop_variable.
    :paramstr loop_variable: Name of the variable that is parallelised.
    :param var_info: VariableAccessInfo
    :return: A pair consisting of a bool, indicating if the variable can \
        be used in parallel, and a message indicating why it can not \
        be parallelised.
    :rtype: (bool, message)
    '''

    # If a variable is read-only, it can be parallelised
    if var_info.is_read_only():
        return (True, "")

    # Now detect which dimension(s) is/are parallelised, i.e.
    # which dimension depends on loop_variable. Also collect all
    # indices that are actually used
    dimension_index = -1
    all_indices = []
    for access in var_info.get_all_accesses():
        indices = access.get_indices()
        # Now determine all dimension that depend on the
        # parallel variable:
        for n, index in enumerate(indices):
            accesses = VariablesAccessInfo()
            index.reference_accesses(accesses)
            try:
                _ = accesses.get_varinfo(loop_variable)
                # This array would be parallelised across different
                # indices (a(i,j), and a(j,i) ):
                if dimension_index > -1 and dimension_index != n:
                    return (False, "Variable '{0}' is using loop variable "
                                   "{1} in index {2} and {3}."
                            .format(var_info.get_var_name(),
                                    loop_variable, dimension_index, n))
                else:
                    dimension_index = n
                all_indices.append(index)
            except KeyError:
                # This dimension does not use the parallel
                # variable
                continue

    # Now we have confirmed that all parallel accesses to the variable
    # are using the same dimension.
    # If all accesses use the same index, then the loop can be parallelised:
    # (this could be tested above, but this way it is a bit clearer for now)
    # TODO: convert the indices back to Fortran!
    first_index = all_indices[0]
    for index in all_indices[1:]:
        if not first_index.math_equal(index):
            return (False, "Variable {0} is using index {1} and {2} and can "
                           "therefore not be parallelised"
                    .format(var_info.get_var_name(), str(first_index),
                            str(index)))
    return (True, "")


def can_loop_be_parallelised(loop, loop_variable=None):
    '''Returns true if the loop can be parallelised along the
    specified variable.'''

    if loop.loop_type != "lat":
        return False
    var_accesses = VariablesAccessInfo()
    loop.reference_accesses(var_accesses)

    loop_vars = [l.variable_name for l in loop.walk([loop], Loop)]

    for var_name in var_accesses.get_all_vars():
        # Ignore all loop variables - they look like reductions because of
        # the write-read access in the loop:
        if var_name in loop_vars:
            continue

        var_info = var_accesses.get_varinfo(var_name)
        if var_info.is_array():
            par_able, message = is_array_parallelisable(loop_variable,
                                                        var_info)
        else:
            # Handle scalar variable
            par_able, message = is_scalar_parallelisable(var_info)
        if not par_able:
            print("Loop not parallelisable: {0}".format(message))

    return True


def create_omp(statements):
    parallel_loop = OMPLoopTrans()
    for statement in statements:
        # Assignments can for now be just done in parallel
        if isinstance(statement, Assignment):
            continue
        if isinstance(statement, NemoLoop):
            var = statement.variable_name
            if can_loop_be_parallelised(statement, var):
                parallel_loop.apply(statement)
        if isinstance(statement, IfBlock):
            create_omp(statement.if_body)
            if statement.else_body:
                create_omp(statement.else_body)


def create_all_omp_directives(statements):

    while statements and isinstance(statements[-1], Assignment):
        del statements[-1]

    # If there were only assignments in a block, don't bother parallelising it
    if statements == []:
        return

    parallel = OMPParallelTrans()
    _, _ = parallel.apply(statements)
    create_omp(statements)


def trans(psy):
    print("Invokes found:")
    print(psy.invokes.names)

    for subroutine in psy.invokes.names:
        sched = psy.invokes.get(subroutine).schedule

        # First step: split the subroutine into blocks, each one consisting
        # of loops, which are then separated by other statements (e.g. calls)
        blocks = []
        collect_loop_blocks(sched, blocks)
        # Now create individual OMP parallel directives around those blocks:
        for statements in blocks:
            if statements != []:
                create_all_omp_directives(statements)

    # sched.view()
    return psy