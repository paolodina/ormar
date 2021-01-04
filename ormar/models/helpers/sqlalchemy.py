import copy
import logging
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple, Type

import sqlalchemy

from ormar import ForeignKey, Integer, ModelDefinitionError  # noqa: I202
from ormar.fields import BaseField, ManyToManyField
from ormar.models.helpers.models import validate_related_names_in_relations
from ormar.models.helpers.pydantic import create_pydantic_field

if TYPE_CHECKING:  # pragma no cover
    from ormar import Model, ModelMeta


def adjust_through_many_to_many_model(
    model: Type["Model"], child: Type["Model"], model_field: Type[ManyToManyField]
) -> None:
    """
    Registers m2m relation on through model.
    Sets ormar.ForeignKey from through model to both child and parent models.
    Sets sqlalchemy.ForeignKey to both child and parent models.
    Sets pydantic fields with child and parent model types.

    :param model: model on which relation is declared
    :type model: Model class
    :param child: model to which m2m relation leads
    :type child: Model class
    :param model_field: relation field defined in parent model
    :type model_field: ManyToManyField
    """
    model_field.through.Meta.model_fields[model.get_name()] = ForeignKey(
        model, real_name=model.get_name(), ondelete="CASCADE"
    )
    model_field.through.Meta.model_fields[child.get_name()] = ForeignKey(
        child, real_name=child.get_name(), ondelete="CASCADE"
    )

    create_and_append_m2m_fk(model, model_field)
    create_and_append_m2m_fk(child, model_field)

    create_pydantic_field(model.get_name(), model, model_field)
    create_pydantic_field(child.get_name(), child, model_field)


def create_and_append_m2m_fk(
    model: Type["Model"], model_field: Type[ManyToManyField]
) -> None:
    """
    Registers sqlalchemy Column with sqlalchemy.ForeignKey leadning to the model.

    Newly created field is added to m2m relation through model Meta columns and table.

    :param model: Model class to which FK should be created
    :type model: Model class
    :param model_field: field with ManyToMany relation
    :type model_field: ManyToManyField field
    """
    pk_alias = model.get_column_alias(model.Meta.pkname)
    pk_column = next((col for col in model.Meta.columns if col.name == pk_alias), None)
    if pk_column is None:  # pragma: no cover
        raise ModelDefinitionError(
            "ManyToMany relation cannot lead to field without pk"
        )
    column = sqlalchemy.Column(
        model.get_name(),
        pk_column.type,
        sqlalchemy.schema.ForeignKey(
            model.Meta.tablename + "." + pk_alias,
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
    )
    model_field.through.Meta.columns.append(column)
    # breakpoint()
    model_field.through.Meta.table.append_column(copy.deepcopy(column))


def check_pk_column_validity(
    field_name: str, field: BaseField, pkname: Optional[str]
) -> Optional[str]:
    """
    Receives the field marked as primary key and verifies if the pkname
    was not already set (only one allowed per model) and if field is not marked
    as pydantic_only as it needs to be a database field.

    :raises ModelDefintionError: if pkname already set or field is pydantic_only
    :param field_name: name of field
    :type field_name: str
    :param field: ormar.Field
    :type field: BaseField
    :param pkname: already set pkname
    :type pkname: Optional[str]
    :return: name of the field that should be set as pkname
    :rtype: str
    """
    if pkname is not None:
        raise ModelDefinitionError("Only one primary key column is allowed.")
    if field.pydantic_only:
        raise ModelDefinitionError("Primary key column cannot be pydantic only")
    return field_name


def sqlalchemy_columns_from_model_fields(
    model_fields: Dict, new_model: Type["Model"]
) -> Tuple[Optional[str], List[sqlalchemy.Column]]:
    """
    Iterates over declared on Model model fields and extracts fields that
    should be treated as database fields.

    If the model is empty it sets mandatory id field as primary key
    (used in through models in m2m relations).

    Triggers a validation of relation_names in relation fields. If multiple fields
    are leading to the same related model only one can have empty related_name param.
    Also related_names have to be unique.

    Trigger validation of primary_key - only one and required pk can be set,
    cannot be pydantic_only.

    Append fields to columns if it's not pydantic_only,
    virtual ForeignKey or ManyToMany field.

    :raises ModelDefinitionError: if validation of related_names fail,
    or pkname validation fails.
    :param model_fields: dictionary of declared ormar model fields
    :type model_fields: Dict[str, ormar.Field]
    :param new_model:
    :type new_model: Model class
    :return: pkname, list of sqlalchemy columns
    :rtype: Tuple[Optional[str], List[sqlalchemy.Column]]
    """
    if len(model_fields.keys()) == 0:
        model_fields["id"] = Integer(name="id", primary_key=True)
        logging.warning(
            "Table {table_name} had no fields so auto "
            "Integer primary key named `id` created."
        )
    validate_related_names_in_relations(model_fields, new_model)
    columns = []
    pkname = None
    for field_name, field in model_fields.items():
        if field.primary_key:
            pkname = check_pk_column_validity(field_name, field, pkname)
        if (
            not field.pydantic_only
            and not field.virtual
            and not issubclass(field, ManyToManyField)
        ):
            columns.append(field.get_column(field.get_alias()))
    return pkname, columns


def populate_meta_tablename_columns_and_pk(
    name: str, new_model: Type["Model"]
) -> Type["Model"]:
    """
    Sets Model tablename if it's not already set in Meta.
    Default tablename if not present is class name lower + s (i.e. Bed becomes -> beds)

    Checks if Model's Meta have pkname and columns set.
    If not calls the sqlalchemy_columns_from_model_fields to populate
    columns from ormar.fields definitions.

    :raises ModelDefinitionError: if pkname is not present raises ModelDefinitionError.
    Each model has to have pk.

    :param name: name of the current Model
    :type name: str
    :param new_model: currently constructed Model
    :type new_model: ormar.models.metaclass.ModelMetaclass
    :return: Model with populated pkname and columns in Meta
    :rtype: ormar.models.metaclass.ModelMetaclass
    """
    tablename = name.lower() + "s"
    new_model.Meta.tablename = (
        new_model.Meta.tablename if hasattr(new_model.Meta, "tablename") else tablename
    )
    pkname: Optional[str]

    if hasattr(new_model.Meta, "columns"):
        columns = new_model.Meta.columns
        pkname = new_model.Meta.pkname
    else:
        pkname, columns = sqlalchemy_columns_from_model_fields(
            new_model.Meta.model_fields, new_model
        )

    if pkname is None:
        raise ModelDefinitionError("Table has to have a primary key.")

    new_model.Meta.columns = columns
    new_model.Meta.pkname = pkname
    return new_model


def populate_meta_sqlalchemy_table_if_required(meta: "ModelMeta") -> None:
    """
    Constructs sqlalchemy table out of columns and parameters set on Meta class.
    It populates name, metadata, columns and constraints.

    :param meta: Meta class of the Model without sqlalchemy table constructed
    :type meta: Model class Meta
    :return: class with populated Meta.table
    :rtype: Model class
    """
    if not hasattr(meta, "table"):
        meta.table = sqlalchemy.Table(
            meta.tablename,
            meta.metadata,
            *[copy.deepcopy(col) for col in meta.columns],
            *meta.constraints,
        )
