"""Patch flask-accepts to support additional Marshmallow fields."""
import json

from flask_accepts import utils
from flask_restx import fields as fr
from gator._vendor.marshmallow_mongoengine.fields import Reference
from marshmallow import fields as ma

utils.type_map.update({
    ma.Enum: utils.make_type_mapper(fr.String),
    Reference: utils.make_type_mapper(fr.String)
})  # type: ignore

print('Patched flask-accepts to support additional Marshmallow fields.'
      ' See src/gator/app/api/resources/patch_swagger.py for details.'
      ' This is a temporary fix until flask-accepts is updated to support'
      ' marshmallow-mongoengine.'
)
