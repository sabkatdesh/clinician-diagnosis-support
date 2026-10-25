import os, httpx
from dotenv import dotenv_values

cfg = dotenv_values(".env")
file_key = cfg.get("AZURE_OPENAI_API_KEY") or ""
sys_key = os.environ.get("AZURE_OPENAI_API_KEY") or ""
dep = cfg.get("AZURE_EMBEDDING_DEPLOYMENT")
print("Windows/PyCharm env var set:", bool(sys_key), "| ends:", sys_key[-4:])
print(".env key ends:", file_key[-4:], "| deployment:", repr(dep))

bases = [
    "https://trip-advisor-resource.services.ai.azure.com/openai/v1",
    "https://trip-advisor-resource.openai.azure.com/openai/v1",
]
for base in bases:
    for style, headers in (("bearer", {"Authorization": f"Bearer {file_key}"}),
                           ("api-key", {"api-key": file_key})):
        r = httpx.post(base + "/embeddings", headers=headers,
                       json={"model": dep, "input": "test"}, timeout=30)
        print(r.status_code, style, base.split("//")[1].split("/")[0], r.text[:100].replace("\n", " "))
