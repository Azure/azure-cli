# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import time
from pathlib import Path

from knack.log import get_logger

from azure.cli.core.aaz import AAZStrArg, has_value

from ..aaz.latest.sshkey import Create as _SSHKeyCreate
from ..aaz.latest.sshkey import GenerateKeyPair as _SSHKeyGenerateKeyPair
from ..aaz.latest.sshkey import Show as _SSHKeyShow


logger = get_logger(__name__)


class SSHKeyCreate(_SSHKeyCreate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.encryption_type = AAZStrArg(
            options=["--encryption-type"],
            help="The encryption type of the SSH keys to be generated.",
            default="RSA",
            enum={"RSA": "RSA", "Ed25519": "Ed25519"},
        )
        return args_schema

    def _handler(self, command_args):
        super(_SSHKeyCreate, self)._handler(command_args)
        self._execute_operations()

        args = self.ctx.args
        if not has_value(args.public_key):
            logger.warning("No public key is provided. A key pair is being generated for you.")
            key_pair = _SSHKeyGenerateKeyPair(cli_ctx=self.cli_ctx)(command_args={
                "resource_group": args.resource_group,
                "ssh_public_key_name": args.ssh_public_key_name,
                "encryption_type": args.encryption_type,
            })
            self._save_key_pair(key_pair)

        return _SSHKeyShow(cli_ctx=self.cli_ctx)(command_args={
            "resource_group": args.resource_group,
            "ssh_public_key_name": args.ssh_public_key_name,
        })

    @staticmethod
    def _save_key_pair(key_pair):
        ssh_path = Path.home().joinpath(".ssh")
        if not ssh_path.exists():
            ssh_path.mkdir(mode=0o700)

        private_key_file = str(ssh_path.joinpath(str(time.time()).replace(".", "_")))
        public_key_file = private_key_file + ".pub"

        # Open with restrictive permissions (0600) so the private key is not readable by other
        # local users. O_CREAT | O_EXCL ensures we only ever write to a brand-new file (guarding
        # against a pre-existing file/symlink at this path), and the mode is applied atomically.
        private_key_fd = os.open(private_key_file, flags=os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode=0o600)
        with os.fdopen(private_key_fd, "w", newline="\n") as file:
            file.write(key_pair["privateKey"])
        logger.warning('Private key is saved to "%s".', private_key_file)

        with open(public_key_file, "w", newline="\n") as file:
            file.write(key_pair["publicKey"])
        logger.warning('Public key is saved to "%s".', public_key_file)
