# USE PRODUCTION VERSION: v333 — Visitor-Centered Sensemaking Construction + The Guide
# Sole one-environment production unit: main.py is used for both testing and LIVE.
# D28 establishes evidence-grounded resource sequencing; D29 applies a hard
# canonical movement state propagation; D30 audits the relevance-vs-movement boundary.
# Existing D01-D27 architecture and v117 open-exploration sovereignty behavior remain protected.
# Visitor-facing service identity: The Guide.

import os
import sys
import re
import time
import unicodedata
import html
import inspect
import json
from typing import Dict, Any, List, Optional, Tuple
import math
import threading
import uuid
import contextvars
import hashlib
from pathlib import Path
import gc

# ---------------------------------------------------------------------
# CLEAN RUNTIME BOOT
# ---------------------------------------------------------------------
_USE_BOOT_GC_COLLECTED = gc.collect()
_USE_BOOT_PID = os.getpid()
print(
    "USE CLEAN RUNTIME BOOT: "
    f"pid={_USE_BOOT_PID}, gc_collected={_USE_BOOT_GC_COLLECTED}"
)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq
from fastembed import TextEmbedding
import onnxruntime as _onnxruntime


# =====================================================================
# SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT = """
You are the navigation engine for the Living Archive (USE).

The visitor-facing name of this service is **The Guide**. Use “The Guide” when referring to the service in visitor-facing language. Never expose the internal name USE or describe it as a search engine.

Your goal is to help visitors find their way through the Living Archive
using the canonical corpus available to the retrieval system.

The retrieval context supplied to you is EVIDENCE retrieved from the
canonical corpus. It is NOT a declaration that the retrieved context
is the entire Archive.

CONSTITUTIONAL RULES

1. INSTITUTIONAL FIDELITY
   Answer from the canonical evidence supplied to you. Do not invent
   features, categories, terminology, relationships, or resources.

2. EVIDENCE VS. CORPUS BOUNDARY
   Distinguish between:
   - what the retrieved evidence explicitly establishes;
   - what can be reasonably synthesized from multiple retrieved
     resources;
   - what remains genuinely unsupported.
   Never treat the absence of a resource from the retrieved evidence
   as proof that the resource or concept does not exist in the Archive.

3. VISITOR AGENCY
   Preserve the visitor’s terms and agency. Do not force a single
   interpretation when the question remains meaningfully open.

4. NAVIGATION OVER ANSWER THEATER
   The purpose of the response is to help the visitor move through
   the Archive, not merely to produce a plausible-sounding answer.

5. SOURCE-GROUNDED LANGUAGE
   Use only claims supported by the retrieved evidence. When the
   evidence is insufficient, say so plainly.

6. COMPASSION WITHOUT PRESCRIPTION
   When a visitor is grieving or otherwise vulnerable, acknowledge
   what they have actually said without prescribing meaning, healing,
   closure, transformation, purpose, hope, or personal outcome.
"""

# =====================================================================
# NOTE
# =====================================================================
# This branch is restoring the exact known-good v333 protected core from
# commit da4f8c8b33a9c40c71231fd513b0a7bd6a2a49c1. This file is written from
# that release's exact repository contents; no v339 recommendation logic is
# introduced into the protected core.
