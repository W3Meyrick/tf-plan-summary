import json
import os
import gitlab

def read_plan_output(plan_output_path):
    with open(plan_output_path) as f:
        plan_output = json.load(f)
    return plan_output

def group_resources_by_type(plan_output):
    resources_by_type = {}
    for resource in plan_output["resource_changes"]:
        resource_type = resource["type"]
        if resource_type not in resources_by_type:
            resources_by_type[resource_type] = {"count": 0, "resources": []}
        resources_by_type[resource_type]["count"] += 1
        resources_by_type[resource_type]["resources"].append(resource)
    return resources_by_type

def construct_summary_table(resources_by_type):
    max_type_length = max(len(t) for t in resources_by_type.keys())
    max_name_length = max(
        len(r["name"]) for r in resource for resource in resources_by_type.values()
    )

    table = []
    for resource_type, resources in resources_by_type.items():
        table.append(
            f"| {resource_type:<{max_type_length}} | {resources['count']:<10} |"
        )
        for resource in resources["resources"]:
            table.append(
                f"| {'':{max_type_length}} | {resource['name']:<{max_name_length}} |"
            )

    return "\n".join(table)

def post_summary_table_to_merge_request(summary_table):
    gl = gitlab.Gitlab(os.environ["CI_API_V4_URL"], private_token=os.environ["CI_JOB_TOKEN"])
    project_id = os.environ["CI_PROJECT_ID"]
    merge_request_iid = os.environ["CI_MERGE_REQUEST_IID"]
    merge_request = gl.projects.get(project_id).merge_requests.get(merge_request_iid)
    merge_request.notes.create({"body": summary_table})

if __name__ == "__main__":
    plan_output = read_plan_output("terraform-plan.json")
    resources_by_type = group_resources_by_type(plan_output)
    summary_table = construct_summary_table(resources_by_type)
    post_summary_table_to_merge_request(summary_table)