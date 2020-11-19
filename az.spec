# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


az_a = Analysis(['src/azure-cli/azure/cli/__main__.py'],
             pathex=['./'],
             binaries=[],
             datas=['ALL_PACKAGE_DATA'],
             hiddenimports=[],
             hookspath=['./scripts/pyinstaller/hooks/az/release/'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

azpip_a = Analysis(['src/pip/main.py'],
             pathex=['./'],
             binaries=[],
             hiddenimports=[],
             hookspath=['./scripts/pyinstaller/hooks/pip/'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

aztelemetry_a = Analysis(['src/azure-cli-telemetry/azure/cli/telemetry/__init__.py'],
             pathex=['./'],
             binaries=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

MERGE((az_a, 'az', 'az'), (azpip_a, 'azpip', 'azpip'), (aztelemetry_a, 'aztelemetry', 'aztelemetry'))

az_pyz = PYZ(az_a.pure, az_a.zipped_data,
             cipher=block_cipher)
az_exe = EXE(az_pyz,
          az_a.scripts,
          [],
          exclude_binaries=True,
          name='az',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
az_coll = COLLECT(az_exe,
               az_a.binaries,
               az_a.zipfiles,
               az_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='az')

azpip_pyz = PYZ(azpip_a.pure, azpip_a.zipped_data,
             cipher=block_cipher)
azpip_exe = EXE(azpip_pyz,
          azpip_a.scripts,
          [],
          exclude_binaries=True,
          name='azpip',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
azpip_coll = COLLECT(azpip_exe,
               azpip_a.binaries,
               azpip_a.zipfiles,
               azpip_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='azpip')

aztelemetry_pyz = PYZ(aztelemetry_a.pure, aztelemetry_a.zipped_data, cipher=block_cipher)
aztelemetry_exe = EXE(aztelemetry_pyz,
          aztelemetry_a.scripts,
          [],
          exclude_binaries=True,
          name='aztelemetry',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
aztelemetry_coll = COLLECT(azpip_exe,
               aztelemetry_a.binaries,
               aztelemetry_a.zipfiles,
               aztelemetry_a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='aztelemetry')
