from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

_SPEC = yaml.safe_load((Path(__file__).resolve().parents[1] / "openapi.yaml").read_text())
_REGISTRY = Registry().with_resource(
    "urn:spec", Resource.from_contents(_SPEC, default_specification=DRAFT202012)
)


def contract_errors(schema: str, body) -> list[str]:
    validator = Draft202012Validator(
        {"$ref": f"urn:spec#/components/schemas/{schema}"}, registry=_REGISTRY
    )
    return [e.message for e in validator.iter_errors(body)]
