USE output boundary: model 'qwen/qwen3.6-27b' reached its generation limit; rejecting incomplete visitor answer.
USE compact output boundary: model 'qwen/qwen3.6-27b' returned no usable visitor answer.
USE generation attempt: 'qwen/qwen3.8-27b'
Execution failed for live Groq model 'qwen/qwen3.8-27b': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
INFO:     122.2.183.58:0 - "POST /api/query HTTP/1.1" 200 OK
==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
USE STARTUP FINGERPRINT: version=v134, fingerprint=USE-v134-explicit-resource-type-selection-preservation-one-environment, file=/opt/render/project/src/main.py

Fetching 5 files:   0%|          | 0/5 [00:00<?, ?it/s]Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.

Fetching 5 files:  20%|██        | 1/5 [00:00<00:00,  4.31it/s]
Fetching 5 files:  80%|████████  | 4/5 [00:00<00:00, 10.76it/s]
Fetching 5 files: 100%|██████████| 5/5 [00:03<00:00,  1.46it/s]
INFO:     Started server process [58]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
INFO:     127.0.0.1:39020 - "HEAD / HTTP/1.1" 200 OK
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [58]
==> Your service is live 🎉
==> 
==> ///////////////////////////////////////////////////////////
==> 
INFO:     35.247.124.215:0 - "GET / HTTP/1.1" 200 OK
==> Available at your primary URL https://living-archive-backend.onrender.com
==> 
==> ///////////////////////////////////////////////////////////
USE orientational frame: primary=general, scores={'systems': 0, 'stewardship': 0, 'inward': 0, 'transition': 0, 'relational': 0}, relational=False
USE adaptive stewardship orientation: inactive, score=0
USE function-targeted retrieval: requested=['substantive exploration and sensemaking', 'visual structural orientation'], candidates=1, diagnostics=['substantive exploration and sensemaking:type=Essay,accepted=0,rejected=8', 'visual structural orientation:type=Reference Map,accepted=1,rejected=7'].
USE retrieval: 12 candidates + 1 function-targeted -> 12 unique resources.
USE D17 relational reasoning: explicit question contrast recognized; multi-resource evidence remains available for bounded synthesis.
USE canonical doorway selection: primary='What If the Old Way of Seeing Things No Longer Works?', score=18, detail=(0, 2, 0, 7, 1, 0, 0, 3, 0), candidates=12.
USE D29 canonical movement: doorway='What If the Old Way of Seeing Things No Longer Works?', destination_validated=True, explicit_next=0, explicit_links=0.
USE evidence sufficiency reconciliation: explicit relational question retained for evidence-bound synthesis despite low lexical fit.
USE generation selection: selected=8, titles=['What If the Old Way of Seeing Things No Longer Works?', 'Document Types of the Living Archive', 'Relationship', 'Sovereignty', 'The Living Archive Method', 'Archive &amp; Practice', 'When Knowledge Is Everywhere', 'Public Vocabulary']
Dynamically loaded live Groq models: ['allam-2-7b', 'groq/compound', 'groq/compound-mini', 'openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.6-27b', 'qwen/qwen3.8-27b']
USE generation candidates: ['allam-2-7b', 'groq/compound', 'groq/compound-mini', 'openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'qwen/qwen3.6-27b', 'qwen/qwen3.8-27b']
USE generation context budget: 1337/1800 chars; max_tokens=320.
USE generation attempt: 'allam-2-7b'
Execution failed for live Groq model 'allam-2-7b': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
USE output boundary: canonical evidence-schema leakage detected; rejecting this model output.
USE compact output boundary: model 'allam-2-7b' returned no usable visitor answer.
USE generation attempt: 'groq/compound'
Execution failed for live Groq model 'groq/compound': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
USE compact generation fallback failed for 'groq/compound': Error code: 413 - {'error': {'message': 'Request Entity Too Large', 'type': 'invalid_request_error', 'code': 'request_too_large'}}
USE generation attempt: 'groq/compound-mini'
Execution failed for live Groq model 'groq/compound-mini': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
USE output boundary: topical response ignored all selected canonical resources for model 'groq/compound-mini'; trying the next live model.
USE compact output boundary: model 'groq/compound-mini' returned no usable visitor answer.
USE generation attempt: 'openai/gpt-oss-120b'
Execution failed for live Groq model 'openai/gpt-oss-120b': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
USE output boundary: model 'openai/gpt-oss-120b' reached its generation limit; rejecting incomplete visitor answer.
USE compact output boundary: model 'openai/gpt-oss-120b' returned no usable visitor answer.
USE generation attempt: 'openai/gpt-oss-20b'
Execution failed for live Groq model 'openai/gpt-oss-20b': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
USE output boundary: model 'openai/gpt-oss-20b' reached its generation limit; rejecting incomplete visitor answer.
USE compact output boundary: model 'openai/gpt-oss-20b' returned no usable visitor answer.
USE generation attempt: 'qwen/qwen3.6-27b'
Execution failed for live Groq model 'qwen/qwen3.6-27b': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
USE output boundary: model 'qwen/qwen3.6-27b' reached its generation limit; rejecting incomplete visitor answer.
USE compact output boundary: model 'qwen/qwen3.6-27b' returned no usable visitor answer.
USE generation attempt: 'qwen/qwen3.8-27b'
Execution failed for live Groq model 'qwen/qwen3.8-27b': USE provider preflight could not fit the fixed system/user envelope: fixed_input=3108, estimated_output=1600.
USE generation compact fallback: 541/650 chars; max_tokens=160.
USE provider preflight: input=1662 chars, estimated_total=2462 chars, max_tokens=160, fixed_input=1121, evidence=541 chars.
INFO:     122.2.183.58:0 - "POST /api/query HTTP/1.1" 200 OK
==> Detected service running on port 10000
==> Docs on specifying a port: https://render.com/docs/web-services#port-binding
INFO:     128.140.8.200:0 - "GET / HTTP/1.1" 200 OK
INFO:     128.140.8.200:0 - "GET / HTTP/1.1" 200 OK
INFO:     128.140.8.200:0 - "GET / HTTP/1.1" 200 OK
==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
==> Deploying...
==> Setting WEB_CONCURRENCY=1 by default, based on available CPUs in the instance
==> Running 'uvicorn main:app --host 0.0.0.0 --port $PORT'
USE STARTUP FINGERPRINT: version=v135, fingerprint=USE-v135-canonical-evidence-enrichment-on-duplicate-one-environment, file=/opt/render/project/src/main.py

Fetching 5 files:   0%|          | 0/5 [00:00<?, ?it/s]Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.

Fetching 5 files:  20%|██        | 1/5 [00:00<00:01,  3.58it/s]
Fetching 5 files:  60%|██████    | 3/5 [00:00<00:00,  7.14it/s]
Fetching 5 files: 100%|██████████| 5/5 [00:03<00:00,  1.24it/s]
Fetching 5 files: 100%|██████████| 5/5 [00:03<00:00,  1.49it/s]
INFO:     Started server process [58]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
INFO:     127.0.0.1:60756 - "HEAD / HTTP/1.1" 200 OK
==> Your service is live 🎉
==> 
==> ///////////////////////////////////////////////////////////
