import argparse
import json
import os
import gitlab

def summarize_terraform_plan(plan_path):
    with open(plan_path) as f:
        plan = json.load(f)

    resource_counts = {}
    for resource in plan['resource_changes']:
        resource_type = resource['type']
        resource_name = resource['name']
        resource_counts[(resource_type, resource_name)] = resource_counts.get((resource_type, resource_name), 0) + 1

    table = []
    table.append(('Resource Type', 'Resource Name', 'Count'))
    table.append(('-------------', '-------------', '-----'))
    for (resource_type, resource_name), count in sorted(resource_counts.items()):
        table.append((resource_type, resource_name, count))

    col_widths = [max(len(str(row[i])) for row in table) for i in range(len(table[0]))]
    format_str = '  '.join(['{{:<{}}}'.format(width) for width in col_widths])
    table_str = '\n'.join([format_str.format(*row) for row in table])

    return table_str

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', help='Path to Terraform plan JSON file', required=True)
    args = parser.parse_args()

    project_id = os.environ.get('CI_PROJECT_ID')
    merge_request_iid = os.environ.get('CI_MERGE_REQUEST_IID')

    gl = gitlab.Gitlab.from_env()
    project = gl.projects.get(project_id)
    merge_request = project.mergerequests.get(merge_request_iid)

    table_str = summarize_terraform_plan(args.path)
    merge_request.notes.create({'body': table_str})

if __name__ == '__main__':
    main()