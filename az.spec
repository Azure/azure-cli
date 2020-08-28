# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src/azure-cli/azure/cli/__main__.py'],
             pathex=['./'],
             binaries=[],
             datas=[('src/azure-cli-core/azure/cli/core/auth_landing_pages/*.html', 'azure/cli/core/auth_landing_pages/'),
             ('src/azure-cli/azure/cli/command_modules/botservice/*.config', 'azure/cli/command_modules/botservice/'),
             ('src/azure-cli/azure/cli/command_modules/botservice/*.json', 'azure/cli/command_modules/botservice/'),
             ('src/azure-cli/azure/cli/command_modules/servicefabric/template/windows/template.json', 'azure/cli/command_modules/servicefabric/template/windows/'),
             ('src/azure-cli/azure/cli/command_modules/servicefabric/template/windows/parameter.json', 'azure/cli/command_modules/servicefabric/template/windows/'),
             ('src/azure-cli/azure/cli/command_modules/servicefabric/template/linux/template.json', 'azure/cli/command_modules/servicefabric/template/linux/'),
             ('src/azure-cli/azure/cli/command_modules/servicefabric/template/linux/parameter.json', 'azure/cli/command_modules/servicefabric/template/linux/'),
             ('src/azure-cli/azure/cli/command_modules/servicefabric/template/service/template.json', 'azure/cli/command_modules/servicefabric/template/service/'),
             ('src/azure-cli/azure/cli/command_modules/servicefabric/template/service/parameter.json', 'azure/cli/command_modules/servicefabric/template/service/'),
             ('src/azure-cli/azure/cli/command_modules/appservice/resources/WindowsFunctionsStacks.json', 'azure/cli/command_modules/appservice/resources/'),
             ('src/azure-cli/azure/cli/command_modules/appservice/resources/LinuxFunctionsStacks.json', 'azure/cli/command_modules/appservice/resources/'),
             ('src/azure-cli/azure/cli/command_modules/appservice/resources/WebappRuntimeStacks.json', 'azure/cli/command_modules/appservice/resources/')],
             hiddenimports=['humanfriendly'],
             hookspath=['./scripts/pyinstaller/hooks/'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='az',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='az')
