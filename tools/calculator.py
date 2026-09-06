"""Safe decimal calculator for expressions found in legal queries."""

import ast
import operator
from decimal import Decimal, DivisionByZero, InvalidOperation


class CalculatorTool:
    name = "Calculator Tool"

    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def run(self, expression: str) -> dict:
        """Evaluate a restricted arithmetic expression using Decimal values."""
        try:
            tree = ast.parse(expression, mode="eval")
            value = self._evaluate(tree.body)
            return {
                "tool": self.name,
                "success": True,
                "input": expression,
                "result": self._format(value),
            }
        except (ArithmeticError, InvalidOperation, SyntaxError, ValueError, TypeError) as exc:
            return {
                "tool": self.name,
                "success": False,
                "input": expression,
                "result": None,
                "error": f"Could not calculate expression: {str(exc)[:200]}",
            }

    def _evaluate(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return Decimal(str(node.value))
        if isinstance(node, ast.UnaryOp) and type(node.op) in self._operators:
            return self._operators[type(node.op)](self._evaluate(node.operand))
        if isinstance(node, ast.BinOp) and type(node.op) in self._operators:
            left = self._evaluate(node.left)
            right = self._evaluate(node.right)
            return self._operators[type(node.op)](left, right)
        raise ValueError("Only numeric arithmetic is supported.")

    @staticmethod
    def _format(value: Decimal) -> str:
        normalized = value.normalize()
        return format(normalized, "f")
