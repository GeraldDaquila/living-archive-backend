# USE PRODUCTION VERSION: v446 — emptiness routing priority
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v446"
DEPLOYMENT_FINGERPRINT = "USE-v446-emptiness-routing-priority"
CANONICAL_BUILD_ID = "USE-BUILD-v446-emptiness-routing-priority"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

# This commit intentionally preserves the complete v445 file and changes only
# the visitor-routing order/priority for the emptiness calibration class.

