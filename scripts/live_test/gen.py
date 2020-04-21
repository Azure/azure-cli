import os

from jinja2 import Environment, FileSystemLoader, select_autoescape


def main():
    env = Environment(loader=FileSystemLoader('./'))
    template = env.get_template('template.yml')
    config = {}
    config['modules'] = get_modules()
    result = template.render(config)
    with open('template_out.yml', 'w') as f:
        f.write(result)


def get_modules():
    """
    :return: str[]
    """
    origin_path = os.getcwd()
    os.chdir('c:/yfy/tmp')
    if not os.path.exists('azure-cli'):
        os.system('git clone -b dev https://github.com/Azure/azure-cli.git')
    if not os.path.exists('azure-cli-extensions'):
        os.system('git clone -b master https://github.com/Azure/azure-cli-extensions.git')
    os.chdir('azure-cli')
    os.system('git pull origin dev')
    os.chdir('../azure-cli-extensions')
    os.system('git pull origin master')
    os.chdir('..')
    path = 'azure-cli/src/azure-cli/azure/cli/command_modules'
    modules = [m for m in os.listdir(path) if os.path.isdir(os.path.join(path, m))]
    # path = 'azure-cli-extensions/src'
    # modules.extend(m for m in os.listdir(path) if os.path.isdir(os.path.join(path, m)))
    os.chdir(origin_path)
    return modules


if __name__ == '__main__':
    main()
