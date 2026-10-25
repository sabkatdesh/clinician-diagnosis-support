import os
import certifi
from dotenv import load_dotenv

load_dotenv(override=True)

os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_FOUNDRY_ENDPOINT = os.environ.get("AZURE_FOUNDRY_ENDPOINT")
AZURE_FOUNDRY_DEPLOYMENT = os.environ.get("AZURE_FOUNDRY_DEPLOYMENT")
AZURE_EMBEDDING_ENDPOINT = os.environ.get("AZURE_EMBEDDING_ENDPOINT")
AZURE_EMBEDDING_DEPLOYMENT = os.environ.get("AZURE_EMBEDDING_DEPLOYMENT")
WEAVIATE_CLUSTER = os.environ.get("WEAVIATE_CLUSTER")
WEAVIATE_API_KEY = os.environ.get("WEAVIATE_API_KEY")
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "ClinicalRAG")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
DOC_PATH = os.environ.get("DOC_PATH")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")
UPSTASH_REDIS_URL = os.environ.get("UPSTASH_REDIS_URL")
