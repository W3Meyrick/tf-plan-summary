import argparse
import json
import prettytable
from typing import List
from enum import Enum
from colorama import Fore, Style
from prettytable import PrettyTable, DOUBLE_BORDER


class Action(Enum):
    CREATE: str = "create"
    UPDATE: str = "update"
    DELETE: str = "delete"


class Change:
    actions: List[Action]


class ResourceChange:
    address: str
    module_address: str
    mode: str
    type: str
    name: str
    provider_name: str
    change: Change


class TerraformPlan:
    format_version: str
    terraform_version: str
    prior_state: dict
    configuration: dict
    planned_values: dict
    # proposed_unknown: dict
    variables: dict
    resource_drift: List[dict]
    output_changes: dict
    resource_changes: List[ResourceChange]


def summarise_as_table(terraform_plan: TerraformPlan, query: str = "") -> str:
    create_list: list[ResourceChange] = []
    update_list: list[ResourceChange] = []
    delete_list: list[ResourceChange] = []

    unique_create_types: dict[str, int] = {}
    unique_update_types: dict[str, int] = {}
    unique_delete_types: dict[str, int] = {}

    for resource_change in terraform_plan.resource_changes:
        actions = resource_change.change.actions
        if query in resource_change.type:
            if Action.CREATE.value in actions:
                create_list.append(resource_change)
                unique_create_types.update({resource_change.type: unique_create_types.get(resource_change.type, 0) + 1})
            elif Action.UPDATE.value in actions:
                update_list.append(resource_change)
                unique_update_types.update({resource_change.type: unique_update_types.get(resource_change.type, 0) + 1})
            elif Action.DELETE.value in actions:
                delete_list.append(resource_change)
                unique_delete_types.update({resource_change.type: unique_delete_types.get(resource_change.type, 0) + 1})
            else:
                print(f"WARN: Unknown resource change change action: {actions}")
    pt: PrettyTable = PrettyTable()
    pt.set_style(DOUBLE_BORDER)
    pt.hrules = prettytable.ALL
    pt.field_names = [Fore.BLUE + "Change" + Style.RESET_ALL, Fore.BLUE + "Name" + Style.RESET_ALL,
                      Fore.BLUE + "Resource Count" + Style.RESET_ALL, Fore.BLUE + "Type" + Style.RESET_ALL,
                      Fore.BLUE + "Type Count" + Style.RESET_ALL]

    pt.add_row([Fore.GREEN + "ADD" + Style.RESET_ALL,
                "\n".join([i.address for i in create_list]),
                len(create_list),
                "\n".join(unique_create_types.keys()),
                "\n".join(map(str, list(unique_create_types.values()))),
                ])

    pt.add_row([Fore.YELLOW + "CHANGE" + Style.RESET_ALL,
                "\n".join([i.address for i in update_list]),
                len(update_list),
                "\n".join(unique_update_types.keys()),
                "\n".join(map(str, list(unique_update_types.values()))),
                ])

    pt.add_row([Fore.RED + "DESTROY" + Style.RESET_ALL,
                "\n".join([i.address for i in delete_list]),
                len(delete_list),
                "\n".join(unique_delete_types.keys()),
                "\n".join(map(str, list(unique_delete_types.values()))),
                ])

    return pt.get_string()


def read_tf_plan_json(json_path):
    with open(json_path) as json_file:
        data = json.load(json_file)
    return data


def extract_actions(change_dict):
    return {
        "actions": change_dict["actions"]
    }


def extract_change(resource_change_dict):
    return {
        "change": extract_actions(resource_change_dict["change"])
    }


def extract_resource_change(resource_change_dict):
    return {
        "address": resource_change_dict["address"],
        "module_address": resource_change_dict["module_address"],
        "mode": resource_change_dict["mode"],
        "type": resource_change_dict["type"],
        "name": resource_change_dict["name"],
        "provider_name": resource_change_dict["provider_name"],
        "change": extract_change(resource_change_dict),
        "action_reason": resource_change_dict.get("action_reason")
    }


def remove_no_op_changes(resource_changes_dicts):
    filtered_changes = []
    for i in resource_changes_dicts:
        if "no-op" not in i["change"]["actions"]:
            filtered_changes.append(extract_resource_change(i))

    return filtered_changes


def dict_to_change(data: dict) -> Change:
    change: Change = Change()
    setattr(change, "actions", data["actions"])
    return change


def dict_to_resource_change(data: List[dict]) -> List[ResourceChange]:
    resource_changes: List[ResourceChange] = []
    for res in data:
        if "no-op" not in res["change"]["actions"]:
            resource_change: ResourceChange = ResourceChange()
            for key, value in res.items():
                if key == "change":
                    value = dict_to_change(value)
                setattr(resource_change, key, value)
            resource_changes.append(resource_change)
    return resource_changes


def dict_to_terraform_plan(data: dict) -> TerraformPlan:
    terraform_plan: TerraformPlan = TerraformPlan()
    for key, value in data.items():
        if key == "resource_changes":
            value = dict_to_resource_change(value)
        setattr(terraform_plan, key, value)
    return terraform_plan


def execute(args):
    data = read_tf_plan_json(args.path)
    terraform_plan = dict_to_terraform_plan(data)
    print(summarise_as_table(terraform_plan, query=args.query))


if __name__ == "__main__":
    my_parser = argparse.ArgumentParser(
        prog="tps",
        description="Terraform Plan Summary"
    )

    # Add the arguments
    my_parser.add_argument(
        "--path",
        metavar="-p",
        type=str,
        help="The path to the JSON Plan file.",
        required=True
    )

    my_parser.add_argument(
        "--query",
        metavar="-q",
        type=str,
        help="Optional query to further filter the resources you are looking at",
        default="",
        required=False
    )

    args = my_parser.parse_args()
    execute(args)
