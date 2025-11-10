#!/usr/bin/make

# SPDX-FileCopyrightText: 2025 Intevation GmbH
#
# SPDX-License-Identifier: Apache-2.0

check:
	codespell --check-filenames
	find . -name '*.sh' -exec shellcheck --severity=warning {} \+

sync:
	rsync -av * .git* --exclude '*.pyc' --exclude __pycache__ --exclude dist euarne.intevation.de:dev/scripts/
