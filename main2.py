import argparse
import json
import gitlab

def parse_tfplan(tfplan_path):
    with open(tfplan_path, 'r') as tfplan_file:
        tfplan = json.load(tfplan_file)

    resources = {}
    for module in tfplan['resource_changes']:
        for change in module['change']:
            if change['actions'][0] == 'create':
                res_type = change['type']
                res_name = change['name']
                if res_type not in resources:
                    resources[res_type] = {}
                resources[res_type][res_name] = change['before'] or change['after']

    return resources


def summarize_resources(resources):
    resource_counts = {}
    for resource_type in resources:
        resource_counts[resource_type] = len(resources[resource_type])

    return resource_counts


def format_summary(summary):
    max_type_length = max(len(resource_type) for resource_type in summary)
    max_count_length = max(len(str(count)) for count in summary.values())
    formatted_summary = 'Resource Type' + ' ' * (max_type_length - len('Resource Type')) + ' | ' + 'Resource Count' + ' ' * (max_count_length - len('Resource Count')) + '\n'
    formatted_summary += '-' * (max_type_length + max_count_length + 3) + '\n'
    for resource_type, resource_count in summary.items():
        formatted_summary += resource_type + ' ' * (max_type_length - len(resource_type)) + ' | ' + str(resource_count) + ' ' * (max_count_length - len(str(resource_count))) + '\n'

    return formatted_summary


def post_mr_comment(project_id, merge_request_iid, summary):
    gl = gitlab.Gitlab.from_config()
    project = gl.projects.get(project_id)
    merge_request = project.mergerequests.get(merge_request_iid)
    merge_request.notes.create({'body': '### Terraform Plan Resource Summary\n\n' + summary})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Summarize Terraform plan output and post as a comment to a GitLab merge request.')
    parser.add_argument('--path', type=str, required=True, help='Path to Terraform plan JSON file')
    parser.add_argument('--project-id', type=int, required=True, help='ID of GitLab project')
    parser.add_argument('--merge-request-iid', type=int, required=True, help='IID of GitLab merge request')
    args = parser.parse_args()

    resources = parse_tfplan(args.path)
    resource_summary = summarize_resources(resources)
    formatted_summary = format_summary(resource_summary)
    post_mr_comment(args.project_id, args.merge_request_iid, formatted_summary)