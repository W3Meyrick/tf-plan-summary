import argparse
import os
import gitlab
from tabulate import tabulate

def parse_args():
    parser = argparse.ArgumentParser(description='Terraform plan summary')
    parser.add_argument('--path', required=True, help='Path to Terraform plan JSON file')
    return parser.parse_args()

def get_gitlab_client():
    gitlab_private_token = os.environ.get('gitlab_private_token')
    gl = gitlab.Gitlab('https://gitlab.com', private_token=gitlab_private_token, api_version='4')
    return gl

def get_merge_request_iid():
    return os.environ.get('CI_MERGE_REQUEST_IID')

def get_resource_counts_and_names(terraform_plan):
    resource_counts = {}
    resource_names = {}
    for resource in terraform_plan['resource_changes']:
        resource_type = resource['type']
        change_type = resource['change']['actions'][0]
        if resource_type not in resource_counts:
            resource_counts[resource_type] = {'create': [], 'update': [], 'delete': []}
            resource_names[resource_type] = {'create': [], 'update': [], 'delete': []}
        resource_counts[resource_type][change_type].append(1)
        resource_names[resource_type][change_type].append(resource['name'])
    return resource_counts, resource_names

def format_resource_summary(resource_counts, resource_names):
    sections = []
    for change_type in ['create', 'update', 'delete']:
        section = []
        for resource_type, counts in resource_counts.items():
            if sum(counts[change_type]) == 0:
                continue
            names = "\n".join(resource_names[resource_type][change_type])
            section.append([resource_type, sum(counts[change_type]), names])
        if len(section) > 0:
            sections.append((change_type.capitalize(), section))
    result = ""
    for section in sections:
        section_name, data = section
        headers = ["Resource Type", "Count", "Names"]
        result += f"{section_name}:\n{tabulate(data, headers, tablefmt='pipe')}\n\n"
    return result.strip()

if __name__ == '__main__':
    args = parse_args()
    with open(args.path, 'r') as f:
        terraform_plan = json.load(f)
    resource_counts, resource_names = get_resource_counts_and_names(terraform_plan)
    resource_summary = format_resource_summary(resource_counts, resource_names)
    gl = get_gitlab_client()
    merge_request_iid = get_merge_request_iid()
    project_id = os.environ.get('CI_PROJECT_ID')
    merge_request = gl.projects.get(project_id).mergerequests.get(merge_request_iid)
    merge_request.notes.create({'body': f'Terraform plan summary:\n{resource_summary}'})