from copy import deepcopy
from dataclasses import dataclass

from schemantic.schema.arg_type_info import ArgNameToTypeInfo, InitArgTypeInfo, OwnerToDefault
from schemantic.schema.model import (
    CommonSignatureModel,
    CultureSchema,
    GroupMemberSchema,
    GroupSchema,
    HomologueSchema,
    SignatureModel,
    SingleSchema,
)
from schemantic.utils.mapping import dict_sorted_by_dict_key


@dataclass(frozen=True, slots=True)
class ExpectedSchemas:
    single_schema: SingleSchema
    homologue_schema: HomologueSchema
    group_schema: GroupSchema
    culture_schema: CultureSchema


def infer_expected_schemas(class_type: type, other_class_type: type) -> ExpectedSchemas:
    def intersecting_signature(owner_to_default: OwnerToDefault) -> ArgNameToTypeInfo:
        return {"we": InitArgTypeInfo(type_hint="string", owner_to_default=owner_to_default)}

    class_name = class_type.__name__
    other_class_name = other_class_type.__name__

    model_signature_to_type_info = dict(
        required={"must_be": InitArgTypeInfo(type_hint="integer")},
        optional=dict_sorted_by_dict_key(
            {
                "age": InitArgTypeInfo(type_hint="Any[integer, None]"),
                "n": InitArgTypeInfo(type_hint="None"),
                "new_age": InitArgTypeInfo(type_hint="Any[integer, string, None]"),
                **intersecting_signature({class_type: "n"}),
            }
        ),
    )
    other_model_signature_to_type_info = intersecting_signature({other_class_type: "m"})

    single_model_signature_with_arg_info = deepcopy(model_signature_to_type_info)
    single_model_signature_with_arg_info["optional"]["we"] = InitArgTypeInfo(
        type_hint="string", owner_to_default={class_type: "n"}
    )

    flattened_signature_with_arg_info = {}
    for arg_info in model_signature_to_type_info.values():
        flattened_signature_with_arg_info.update(arg_info)
    flattened_signature_with_arg_info.update(intersecting_signature({class_type: "n", other_class_type: "m"}))

    common_schema = CommonSignatureModel.model_validate(model_signature_to_type_info, from_attributes=True)
    common_schema.optional.update(intersecting_signature({class_type: "n", other_class_type: "m"}))

    single_schema = SingleSchema(
        class_name=class_name, defined={"must_be": None}, **single_model_signature_with_arg_info
    )

    homologue_schema = HomologueSchema(
        class_name=class_name,
        common={},
        instances={
            "test_1": {},
            "test_2": {},
        },
        init_signature=SignatureModel(**single_model_signature_with_arg_info),
    )

    group_schema = GroupSchema(
        common=common_schema,
        members={
            class_name: GroupMemberSchema(
                class_name=class_name,
                **model_signature_to_type_info,
            ),
            other_class_name: GroupMemberSchema(
                class_name=other_class_name, optional=other_model_signature_to_type_info
            ),
        },
        argument_to_typing=flattened_signature_with_arg_info,
    )

    culture_schema = CultureSchema(
        culture={
            "single_test": single_schema,
            "homologue_test": homologue_schema,
            "group_test": group_schema,
        },
        argument_to_typing=flattened_signature_with_arg_info,
    )

    return ExpectedSchemas(
        single_schema=single_schema,
        homologue_schema=homologue_schema,
        group_schema=group_schema,
        culture_schema=culture_schema,
    )
