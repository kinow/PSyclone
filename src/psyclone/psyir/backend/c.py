# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2019, Science and Technology Facilities Council
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
# Author S. Siso, STFC Daresbury Lab.

'''C PSyIR backend. Generates C code from PSyIR nodes.
Currently limited to just a few PSyIR nodes to support the OpenCL generation,
it needs to be extended for generating pure C code.

'''

from psyclone.psyir.backend.base import PSyIRVisitor, VisitorError


class CWriter(PSyIRVisitor):
    '''Implements a PSyIR-to-C back-end for the PSyIR AST.

    '''

    def gen_declaration(self, symbol):
        '''
        Generates string representing the C declaration of the symbol. In C
        declarations can be found be inside the argument list or with the
        statments, so no indention or punctuation is generated by this method.

        :param symbol: The symbol instance.
        :type symbol: :py:class:`psyclone.psyGen.Symbol`

        :returns: The C declaration of the given of the symbol.
        :rtype: str
        :raises NotImplementedError: if there are some symbol types or nodes \
            which are not implemented yet.
        '''
        code = ""
        if symbol.datatype == "real":
            code = code + "double "
        elif symbol.datatype == "integer":
            code = code + "int "
        elif symbol.datatype == "character":
            code = code + "char "
        elif symbol.datatype == "boolean":
            code = code + "bool "
        else:
            raise NotImplementedError(
                "Could not generate the C definition for the variable '{0}', "
                "type '{1}' is currently not supported."
                "".format(symbol.name, symbol.datatype))

        # If the argument is an array, in C language we define it
        # as an unaliased pointer.
        if symbol.is_array:
            code += "* restrict "

        code += symbol.name
        return code

    def gen_local_variable(self, symbol):
        '''
        Generate C code that declares all local symbols in the Symbol Table.

        :param symbol: The symbol instance.
        :type symbol: :py:class:`psyclone.psyGen.Symbol`

        :returns: C languague declaration of a local variable.
        :rtype: str
        '''
        return "{0}{1};\n".format(self._nindent, self.gen_declaration(symbol))

    def assignment_node(self, node):
        '''This method is called when an Assignment instance is found in the
        PSyIR tree.

        :param node: An Assignment PSyIR node.
        :type node: :py:class:`psyclone.psyGen.Assigment`

        :returns: The C code as a string.
        :rtype: str

        '''
        lhs = self._visit(node.lhs)
        rhs = self._visit(node.rhs)

        result = "{0}{1} = {2};\n".format(self._nindent, lhs, rhs)
        return result

    def reference_node(self, node):
        '''This method is called when a Reference instance is found in the
        PSyIR tree.

        :param node: A Reference PSyIR node.
        :type node: :py:class:`psyclone.psyGen.Reference`

        :returns: The C code as a string.
        :rtype: str

        :raises VisitorError: If this node has children.

        '''
        if node.children:
            raise VisitorError(
                "PSyIR Reference node should not have any children.")
        return node.name

    def array_node(self, node):
        '''This method is called when an Array instance is found in the PSyIR
        tree.

        :param node: An Array PSyIR node.
        :type node: :py:class:`psyclone.psyGen.Array`

        :returns: The C code as a string.
        :rtype: str

        :raises VisitorError: If this node has children.

        '''
        code = node.name + "["

        dimensions_remaining = len(node.children)
        if dimensions_remaining < 1:
            raise VisitorError("Array must have at least 1 dimension.")

        # In C array expressions should be reversed from the PSyIR order
        # (column-major to row-major order) and flattened (1D).
        for child in reversed(node.children):
            code = code + self._visit(child)
            # For each dimension bigger than one, it needs to write the
            # appropriate operation to flatten the array. By convention,
            # the array dimensions are <name>LEN<DIM>.
            # (e.g. A[3,5,2] -> A[3 * ALEN2 * ALEN1 + 5 * ALEN1 + 2])
            for dim in reversed(range(1, dimensions_remaining)):
                dimstring = node.name + "LEN" + str(dim)
                code = code + " * " + dimstring
            dimensions_remaining = dimensions_remaining - 1
            code = code + " + "

        code = code[:-3] + "]"  # Delete last ' + ' and close bracket
        return code

    def literal_node(self, node):
        '''This method is called when a Literal instance is found in the PSyIR
        tree.

        :param node: A Literal PSyIR node.
        :type node: :py:class:`psyclone.psyGen.Literal`

        :returns: The C code as a string.
        :rtype: str

        '''
        result = node.value
        # C Scientific notation is always an 'e' letter
        result = result.replace('d', 'e')
        result = result.replace('D', 'e')
        return result

    def ifblock_node(self, node):
        '''This method is called when an IfBlock instance is found in the
        PSyIR tree.

        :param node: An IfBlock PSyIR node.
        :type node: :py:class:`psyclone.psyGen.IfBlock`

        :returns: The C code as a string.
        :rtype: str

        '''
        if len(node.children) < 2:
            raise VisitorError(
                "IfBlock malformed or incomplete. It should have at least "
                "2 children, but found {0}.".format(len(node.children)))

        condition = self._visit(node.children[0])

        self._depth += 1
        if_body = ""
        for child in node.if_body:
            if_body += self._visit(child)
        else_body = ""
        # node.else_body is None if there is no else clause.
        if node.else_body:
            for child in node.else_body:
                else_body += self._visit(child)
        self._depth -= 1

        if else_body:
            result = (
                "{0}if ({1}) {{\n"
                "{2}"
                "{0}}} else {{\n"
                "{3}"
                "{0}}}\n"
                "".format(self._nindent, condition, if_body, else_body))
        else:
            result = (
                "{0}if ({1}) {{\n"
                "{2}"
                "{0}}}\n"
                "".format(self._nindent, condition, if_body))
        return result

    def unaryoperation_node(self, node):
        '''This method is called when a UnaryOperation instance is found in
        the PSyIR tree.

        :param node: A UnaryOperation PSyIR node.
        :type node: :py:class:`psyclone.psyGen.UnaryOperation`

        :returns: The C code as a string.
        :rtype: str

        :raises VisitorError: If this node has more than one children.

        '''
        if len(node.children) != 1:
            raise VisitorError(
                "UnaryOperation malformed or incomplete. It "
                "should have exactly 1 child, but found {0}."
                "".format(len(node.children)))

        def operator_format(operator_str, expr_str):
            '''
            :param str operator_str: String representing the operator.
            :param str expr_str: String representation of the operand.

            :returns: C language operator expression.
            :rtype: str
            '''
            return "(" + operator_str + expr_str + ")"

        def function_format(function_str, expr_str):
            '''
            :param str function_str: Name of the function.
            :param str expr_str: String representation of the operand.

            :returns: C language unary function expression.
            :rtype: str
            '''
            return function_str + "(" + expr_str + ")"

        # Define a map with the operator string and the formatter function
        # associated with each UnaryOperation.Operator
        from psyclone.psyGen import UnaryOperation
        opmap = {
            UnaryOperation.Operator.MINUS: ("-", operator_format),
            UnaryOperation.Operator.PLUS: ("+", operator_format),
            UnaryOperation.Operator.NOT: ("!", operator_format),
            UnaryOperation.Operator.SIN: ("sin", function_format),
            UnaryOperation.Operator.COS: ("cos", function_format),
            UnaryOperation.Operator.TAN: ("tan", function_format),
            UnaryOperation.Operator.ASIN: ("asin", function_format),
            UnaryOperation.Operator.ACOS: ("acos", function_format),
            UnaryOperation.Operator.ATAN: ("atan", function_format),
            UnaryOperation.Operator.ABS: ("abs", function_format),
            UnaryOperation.Operator.REAL: ("float", function_format),
            UnaryOperation.Operator.SQRT: ("sqrt", function_format),
            }

        # If the instance operator exists in the map, use its associated
        # operator and formatter to generate the code, otherwise raise
        # an Error.
        try:
            opstring, formatter = opmap[node.operator]
        except KeyError:
            raise NotImplementedError(
                "The C backend does not support the '{0}' operator."
                "".format(node.operator))

        return formatter(opstring, self._visit(node.children[0]))

    def binaryoperation_node(self, node):
        '''This method is called when a BinaryOperation instance is found in
        the PSyIR tree.

        :param node: A BinaryOperation PSyIR node.
        :type node: :py:class:`psyclone.psyGen.BinaryOperation`

        :returns: The C code as a string.
        :rtype: str

        '''
        if len(node.children) != 2:
            raise VisitorError(
                "BinaryOperation malformed or incomplete. It "
                "should have exactly 2 children, but found {0}."
                "".format(len(node.children)))

        def operator_format(operator_str, expr1, expr2):
            '''
            :param str operator_str: String representing the operator.
            :param str expr1: String representation of the LHS operand.
            :param str expr2: String representation of the RHS operand.

            :returns: C language operator expression.
            :rtype: str
            '''
            return "(" + expr1 + " " + operator_str + " " + expr2 + ")"

        def function_format(function_str, expr1, expr2):
            '''
            :param str function_str: Name of the function.
            :param str expr1: String representation of the first operand.
            :param str expr2: String representation of the second operand.

            :returns: C language binary function expression.
            :rtype: str
            '''
            return function_str + "(" + expr1 + ", " + expr2 + ")"

        # Define a map with the operator string and the formatter function
        # associated with each BinaryOperation.Operator
        from psyclone.psyGen import BinaryOperation
        opmap = {
            BinaryOperation.Operator.ADD: ("+", operator_format),
            BinaryOperation.Operator.SUB: ("-", operator_format),
            BinaryOperation.Operator.MUL: ("*", operator_format),
            BinaryOperation.Operator.DIV: ("/", operator_format),
            BinaryOperation.Operator.REM: ("%", operator_format),
            BinaryOperation.Operator.POW: ("pow", function_format),
            BinaryOperation.Operator.EQ: ("==", operator_format),
            BinaryOperation.Operator.NE: ("!=", operator_format),
            BinaryOperation.Operator.LT: ("<", operator_format),
            BinaryOperation.Operator.LE: ("<=", operator_format),
            BinaryOperation.Operator.GT: (">", operator_format),
            BinaryOperation.Operator.GE: (">=", operator_format),
            BinaryOperation.Operator.AND: ("&&", operator_format),
            BinaryOperation.Operator.OR: ("||", operator_format),
            BinaryOperation.Operator.SIGN: ("copysign", function_format),
            }

        # If the instance operator exists in the map, use its associated
        # operator and formatter to generate the code, otherwise raise
        # an Error.
        try:
            opstring, formatter = opmap[node.operator]
        except KeyError:
            raise VisitorError(
                "The C backend does not support the '{0}' operator."
                "".format(node.operator))

        return formatter(opstring,
                         self._visit(node.children[0]),
                         self._visit(node.children[1]))

    def return_node(self, _):
        '''This method is called when a Return instance is found in
        the PSyIR tree.

        :param node: A Return PSyIR node.
        :type node: :py:class:`psyclone.psyGen.Return`

        :returns: The C code as a string.
        :rtype: str

        '''
        return "{0}return;\n".format(self._nindent)

    def codeblock_node(self, node):
        '''This method is called when a CodeBlock instance is found in the
        PSyIR tree. At the moment all CodeBlocks contain Fortran fparser
        code.

        :param node: A CodeBlock PSyIR node.
        :type node: :py:class:`psyclone.psyGen.CodeBlock`

        :raises VisitorError: The CodeBlock can not be translated to C.

        '''
        raise VisitorError("CodeBlocks can not be translated to C.")
