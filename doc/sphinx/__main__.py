#!/usr/bin/env python3
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# -*- coding: utf-8 -*-

import os
import sphinx

BUILD_DIR = '_build'
FORMAT = 'xml'

argv = ['sphinx-build', '', 'xml', os.getcwd(), BUILD_DIR]
sphinx.make_main(argv)
