The git hooks are available for **azure-cli** and **azure-cli-extensions** repos. They could help you run required checks before creating the PR. 

Please sync the latest code with latest dev branch (for **azure-cli**) or main branch (for **azure-cli-extensions**). 
After that please run the following commands to enable git hooks:

```bash
pip install azdev --upgrade
azdev setup -c <your azure-cli repo path> -r <your azure-cli-extensions repo path>

```
