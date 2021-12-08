set -ev

BOT_TOKEN=$(az keyvault secret show --vault-name REDACTED --name REDACTED --query value -otsv)
# update doc
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
# copy history notes
ESCAPED_CLI_VERSION=`echo "$CLI_VERSION" | sed 's/\./\\\./g'`
ESCAPED_PRE_VERSION=`echo "$PRE_VERSION" | sed 's/\./\\\./g'`
sed -n '/'"$ESCAPED_CLI_VERSION"'/,/'"$ESCAPED_PRE_VERSION"'/p' ../azure-cli/src/azure-cli/HISTORY.rst| sed '1d;2d;$d'| sed '$d' | sed 's| (#[0-9]\+)$||' | tee note.tmp
RELEASE_DATE=$(date -d "next tuesday" '+%B %d, %Y')
MODIFY_DATE=$(date -d "next tuesday" '+%m/%d/%Y')
sed -i "s|^ms.date.*$|ms.date: ${MODIFY_DATE}|g" docs-ref-conceptual/release-notes-azure-cli.md
sed -i '/# \[Current release notes\].*$/ r note.tmp' docs-ref-conceptual/release-notes-azure-cli.md
sed -i '/# \[Current release notes\].*$/a \\n## '"${RELEASE_DATE}"'\n\nVersion '"${CLI_VERSION}"'' docs-ref-conceptual/release-notes-azure-cli.md
sed -i 's/^\*\*\(.*\)\*\*$/### \1/g' docs-ref-conceptual/release-notes-azure-cli.md
sed -i "s|^ms.date.*$|ms.date: ${MODIFY_DATE}|g" docs-ref-conceptual/includes/current-version.md
sed -i 's/'"$PRE_VERSION"'/'"$CLI_VERSION"'/g' docs-ref-conceptual/includes/current-version.md
git commit -am "azure-cli release notes ${CLI_VERSION}"
git push origin ${DOC_BRANCH_NAME}
curl \
  --user "anything:${BOT_TOKEN}" \
  -d "{\"title\":\"release note for azure cli ${CLI_VERSION}\",\"head\":\"${BOT_ACCOUNT_NAME}:${DOC_BRANCH_NAME}\",\"base\":\"main\"}" \
  https://api.github.com/repos/MicrosoftDocs/azure-docs-cli/pulls
