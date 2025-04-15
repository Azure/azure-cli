# This script is used by release pipeline task "Release Notes" to update
# https://github.com/MicrosoftDocs/azure-docs-cli.
#
# It does several things:
# 1. Transfer release notes from src/azure-cli/HISTORY.rst to docs-ref-conceptual/release-notes-azure-cli.md
# 2. Update ms.date
# 3. Update version number in docs-ref-conceptual/includes/current-version.md

# sed manual: https://www.gnu.org/software/sed/manual/sed.html

set -ev

BOT_TOKEN=$(az keyvault secret show --vault-name "${BOT_VAULT_NAME}" --name "${BOT_SECRET_NAME}" --query value -otsv)

git clone https://github.com/Azure/azure-cli.git
cd azure-cli
git config --local user.email "AzPyCLI@microsoft.com"
git config --local user.name "Azure CLI Team"
git remote rename origin upstream
git checkout -b main upstream/main
PRE_VERSION=$(sed -n -e 's/.*__version__.*"\(.*\)"/\1/p' src/azure-cli/azure/cli/__main__.py)
git checkout -b release upstream/release
cd ..
git clone https://github.com/MicrosoftDocs/azure-docs-cli.git
cd azure-docs-cli
git config --local user.email "AzPyCLI@microsoft.com"
git config --local user.name "Azure CLI Team"
git remote rename origin upstream
git remote add origin https://anything:${BOT_TOKEN}@github.com/${BOT_ACCOUNT_NAME}/azure-docs-cli.git
DOC_BRANCH_NAME="cli-release-notes-${CLI_VERSION}"
git checkout -b ${DOC_BRANCH_NAME}

# Copy release notes
# 2\.31\.0
ESCAPED_CLI_VERSION=`echo "$CLI_VERSION" | sed 's/\./\\\./g'`
# 2\.30\.0
ESCAPED_PRE_VERSION=`echo "$PRE_VERSION" | sed 's/\./\\\./g'`
# The 1st sed finds all lines between (including) 2.31.0 and 2.30.0
#   1:             2.31.0
#   2:             ++++++
#                  ...
#   2nd last line:
#   last line:     2.30.0
# The 2nd sed deletes line 1, 2 and last line
# The 3rd sed deletes the last line
# The 4th sed deletes all PR numbers, like (#20233)
sed -n '/'"$ESCAPED_CLI_VERSION"'/,/'"$ESCAPED_PRE_VERSION"'/p' ../azure-cli/src/azure-cli/HISTORY.rst| sed '1d;2d;$d'| sed '$d' | sed 's| (#[0-9]\+)$||' | tee note.tmp
# December 14, 2021
RELEASE_DATE=$(date -d "next tuesday" '+%B %d, %Y')
# 12/14/2021
MODIFY_DATE=$(date -d "next tuesday" '+%m/%d/%Y')
# Update ms.date
sed -i "s|^ms.date.*$|ms.date: ${MODIFY_DATE}|g" docs-ref-conceptual/release-notes-azure-cli.md
# Find the top level heading '# Azure CLI release notes' and append content of note.tmp after it.
sed -i '/^# .*$/ r note.tmp' docs-ref-conceptual/release-notes-azure-cli.md
# Find the top level heading '# Azure CLI release notes' and append lines:
#   # December 7, 2021
#
#   Version 2.31.0
sed -i '/^# .*$/a \\n## '"${RELEASE_DATE}"'\n\nVersion '"${CLI_VERSION}"'' docs-ref-conceptual/release-notes-azure-cli.md
# Update bold text like '**ARM**' to markdown heading '### ARM'
sed -i 's/^\*\*\(.*\)\*\*$/### \1/g' docs-ref-conceptual/release-notes-azure-cli.md

# Update ms.date
sed -i "s|^ms.date.*$|ms.date: ${MODIFY_DATE}|g" docs-ref-conceptual/includes/current-version.md
# Update current version
sed -i 's/'"$PRE_VERSION"'/'"$CLI_VERSION"'/g' docs-ref-conceptual/includes/current-version.md

git commit -am "azure-cli release notes ${CLI_VERSION}"
git push origin ${DOC_BRANCH_NAME}
curl \
  --user "anything:${BOT_TOKEN}" \
  -d "{\"title\":\"release note for azure cli ${CLI_VERSION}\",\"head\":\"${BOT_ACCOUNT_NAME}:${DOC_BRANCH_NAME}\",\"base\":\"main\"}" \
  https://api.github.com/repos/MicrosoftDocs/azure-docs-cli/pulls
