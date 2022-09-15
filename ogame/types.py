from __future__ import unicode_literals
import json
from typing import Optional, DefaultDict, Dict
from collections import defaultdict
from graphene.types.scalars import MAX_INT, MIN_INT, Scalar
from graphql.language.ast import (BooleanValue, FloatValue, IntValue,
                                  ListValue, ObjectValue, StringValue)


class DynamicScalar(Scalar):
    """
    The `DynamicScalar` scalar type represents a JSON object with unknown fields

    Adapted from original type, GenericScalar
    """

    @staticmethod
    def identity(value):
        try:
            return value._asdict()
        except:
            return value

    serialize = identity
    parse_value = identity

    @staticmethod
    def parse_literal(ast):
        if isinstance(ast, (StringValue, BooleanValue)):
            return ast.value
        elif isinstance(ast, IntValue):
            num = int(ast.value)
            if MIN_INT <= num <= MAX_INT:
                return num
        elif isinstance(ast, FloatValue):
            return float(ast.value)
        elif isinstance(ast, ListValue):
            return [DynamicScalar.parse_literal(value) for value in ast.values]
        elif isinstance(ast, ObjectValue):
            return {field.name.value: DynamicScalar.parse_literal(field.value) for field in ast.fields}
        else:
            return None


class CompressedDict:
    """
    Comprime um dicionário em formato binário para armazenamento robusto.
    """
    def __init__(self, data: Dict[str, int]) -> None:
        self._compress(data)

    def _compress(self, data: Dict[str, int]) -> None:
        self.bit_string = json.dumps(data).encode('utf-8')

    def decompress(self) -> DefaultDict[str, int]:
        return json.loads(self.bit_string.decode('utf-8'))

    @staticmethod
    def decompress_bytes(bit_string: bytes) -> Dict[str, int]:
        data = json.loads(bit_string.decode('utf-8')) if bit_string else {}
        return defaultdict(int, data)

    def __repr__(self) -> str:
        return repr(self.decompress())

    def __getitem__(self, key: str) -> Optional:
        return self.decompress().get(key)
