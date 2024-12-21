import abc
import base64
import json
from dataclasses import fields
from typing import Any, Callable

import numpy as np
from numpy.typing import NDArray

SerializableDict = dict[str, Any]
Serializer = Callable[[Any], SerializableDict]
DeSerializer = Callable[[SerializableDict], Any]

TYPE_KEY = "__type__"


def serialize_ndarray(obj: NDArray) -> SerializableDict:
    return {
        TYPE_KEY: "ndarray",
        "shape": list(obj.shape),
        "dtype": str(obj.dtype),
        "base64_data": base64.b64encode(obj).decode(encoding="utf-8"),
    }


def deserialize_ndarray(mapping: SerializableDict) -> NDArray:
    data_bytes = bytearray(mapping["base64_data"], encoding="utf-8")
    return np.frombuffer(
        base64.b64decode(data_bytes), dtype=mapping["dtype"]
    ).reshape(mapping["shape"])


SERIALIZERS: dict[str, Serializer] = {"ndarray": serialize_ndarray}
DESERIALIZERS: dict[str, DeSerializer] = {"ndarray": deserialize_ndarray}


def type_key_adder(serializer: Serializer) -> Serializer:
    def decorated(obj: Any) -> SerializableDict:
        return serializer(obj) | {TYPE_KEY: type(obj).__name__}

    return decorated


def type_key_remover(deserializer: DeSerializer) -> DeSerializer:
    def decorated(mapping: SerializableDict) -> Any:
        mapping.pop(TYPE_KEY)
        return deserializer(mapping)

    return decorated


class JSONSerializable(abc.ABC):
    """
    Mixin to make any class JSON serializable.
    """

    def __init_subclass__(cls):
        SERIALIZERS[cls.__name__] = type_key_adder(cls._to_dict)
        DESERIALIZERS[cls.__name__] = type_key_remover(cls._from_dict)

    @abc.abstractmethod
    def _to_dict(self) -> dict[str, Any]:
        """
        Convert to JSON-serializable dict.
        """

    @classmethod
    @abc.abstractmethod
    def _from_dict(cls, mapping: dict[str, Any]):
        """
        Initialize object from dict loaded from JSON.
        """


def shallow_asdict(obj) -> dict[str, Any]:
    """
    Non-recursive version of dataclasses.asdict().
    """
    return {f.name: getattr(obj, f.name) for f in fields(obj)}


class JSONSerializableDataclass(JSONSerializable):
    def _to_dict(self) -> dict[str, Any]:
        # We don't want to use asdict() here, because it also applies to fields
        # that are dataclasses such as Stats, converting them into dicts
        # along the way. However, we want our code to add the special dict key
        # that defines the data type.
        return shallow_asdict(self)

    @classmethod
    def _from_dict(cls, mapping: dict[str, Any]):
        return cls(**mapping)


class Encoder(json.JSONEncoder):
    def default(self, obj):
        serialize = SERIALIZERS.get(type(obj).__name__, None)
        if serialize:
            return serialize(obj)
        return json.JSONEncoder.default(self, obj)


def object_hook(obj):
    if isinstance(obj, dict) and TYPE_KEY in obj:
        cls_name = obj[TYPE_KEY]
        deserialize = DESERIALIZERS[cls_name]
        return deserialize(obj)
    return obj


def json_dumps(obj, **kwargs):
    kwargs["cls"] = Encoder
    return json.dumps(obj, **kwargs)


def json_loads(s: str, **kwargs):
    kwargs["object_hook"] = object_hook
    return json.loads(s, **kwargs)


def json_dump(obj, fp, **kwargs):
    kwargs["cls"] = Encoder
    return json.dump(obj, fp, **kwargs)


def json_load(fp, **kwargs):
    kwargs["object_hook"] = object_hook
    return json.load(fp, **kwargs)
