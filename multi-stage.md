# Templating GitLab CI Jobs

To template GitLab CI jobs using Python 3 Jinja2 templates and meet the given requirements, you can follow the steps below:

## Step 1: Install the necessary packages
Make sure you have Python 3 installed on your system. Install the Jinja2 library using pip:

```bash
pip install jinja2
```

## Step 2: Create the template file
Create a Jinja2 template file, for example, .gitlab/deployments/template.j2, that contains the common structure for all deployments. Here's an example:

```python
{% for job in jobs %}
{{ job.name }}:
  script:
    - echo "Running {{ job.name }}"
    # Additional steps for the job
{% endfor %}
```

## Step 3: Create the configuration file
Create a configuration file named .gitlab/tfconfig.yml with the following structure:

```yaml
deployments:
  - name: environment1
    jobs:
      - name: job1
        # Additional variables for job1
      - name: job2
        # Additional variables for job2
  - name: environment2
    jobs:
      - name: job3
        # Additional variables for job3
      - name: job4
        # Additional variables for job4
      - name: job5
        # Additional variables for job5
```

## Step 4: Create the Python script
Create a Python script, for example, template_ci_jobs.py, with the following code:

```python
import os
import sys
import yaml
from jinja2 import Environment, FileSystemLoader

# Load the configuration file
with open('.gitlab/tfconfig.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

# Check if there are more than 5 jobs defined
for deployment in config['deployments']:
    if len(deployment['jobs']) > 5:
        print('Error: More than 5 jobs defined in the configuration file.')
        sys.exit(1)

# Create the Jinja2 environment
template_dir = '.gitlab/deployments'
env = Environment(loader=FileSystemLoader(template_dir))

# Template each deployment
for deployment in config['deployments']:
    deployment_name = deployment['name']
    deployment_jobs = deployment['jobs']

    # Render the template with the deployment's variables
    template = env.get_template('template.j2')
    rendered_template = template.render(jobs=deployment_jobs)

    # Create the deployment YAML file
    deployment_file = os.path.join(template_dir, f'{deployment_name}.yml')
    with open(deployment_file, 'w') as file:
        file.write(rendered_template)
```

Using pre-defined templates per environment, this is one option: 

```python
import os
from jinja2 import Environment, FileSystemLoader
import yaml

# Set up the Jinja2 environment
templates_dir = '.gitlab/deployments'
env = Environment(loader=FileSystemLoader(templates_dir))

# Load the jobs from .gitlab/config.yml
config_file = '.gitlab/config.yml'
with open(config_file, 'r') as file:
    config = yaml.safe_load(file)

# Check if the number of jobs exceeds the limit
if len(config['jobs']) > 5:
    raise ValueError("The maximum supported number of jobs is 5.")

# Loop through the template files and render them
for template_file in os.listdir(templates_dir):
    if template_file.endswith('.j2'):
        template = env.get_template(template_file)
        job_name = os.path.splitext(template_file)[0]  # Extract the job name from the template filename
        job_data = next((job for job in config['jobs'] if job['name'] == job_name), None)  # Retrieve the job data

        if job_data:
            variables = job_data.get('variables', {})  # Retrieve the variables for the current job
            rendered_template = template.render(variables)

            # Remove the .j2 extension from the template filename
            rendered_filename = os.path.join(
                templates_dir, os.path.splitext(template_file)[0]
            )

            # Write the rendered template to a file
            with open(rendered_filename, 'w') as file:
                file.write(rendered_template)
        else:
            print(f"Job data not found for '{job_name}'.")
```

## Step 5: Add the script to your GitLab CI pipeline
Add a new stage at the beginning of your GitLab CI pipeline configuration file (e.g., .gitlab-ci.yml) to run the Python script before any other jobs:

```yaml
stages:
  - template_ci_jobs
  # Other stages and jobs...

template_ci_jobs:
  stage: template_ci_jobs
  script:
    - python template_ci_jobs.py
```

This will ensure that the CI pipeline first templates the jobs based on the provided configuration.

Make sure the Python script, template file, and configuration file are committed and pushed to your GitLab repository. When the CI pipeline runs, it will generate the deployment YAML files based on the configuration and place them in the .gitlab/deployments directory.

Note: Ensure that the script file (template_ci_jobs.py) and the template file (template.j2) are in the same directory when executing the script.
