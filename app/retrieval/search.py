import os
from typing import Dict, List, Optional

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import MetadataQuery, Filter
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

try:
    import cohere
except ImportError:
    cohere = None

load_dotenv()

WEAVIATE_CLUSTER = os.getenv("WEAVIATE_CLUSTER")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")
AZURE_FOUNDRY_ENDPOINT = os.getenv("AZURE_FOUNDRY_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_EMBEDDING_DEPLOYMENT")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

from app.config import COLLECTION_NAME

K = 250
ALPHA = 0.5
TOP_N = 15
USE_RERANK = True


# ---------------- INTENT ----------------
INTENT_TO_SUBSECTION = {
    "treatment": {"treatment"},
    "diagnosis": {"diagnosis", "clinical_manifestations"},
    "investigation": {"diagnosis"},
    "prognosis": {"prognosis"},
    "general": set(),
}


def detect_intent(query: str) -> str:
    q = query.lower()

    if any(x in q for x in [
        "treatment", "management", "medication", "therapy", "drug",
        "inhaled", "supportive care"
    ]):
        return "treatment"

    if any(x in q for x in [
        "diagnosis", "diagnostic", "criteria", "clinical features",
        "presentation", "signs", "symptoms", "evaluation", "differential"
    ]):
        return "diagnosis"

    if any(x in q for x in [
        "investigation", "investigations", "test", "tests", "lab",
        "laboratory", "imaging", "echo", "echocardiography"
    ]):
        return "investigation"

    if any(x in q for x in [
        "prognosis", "outcome", "complication", "follow up"
    ]):
        return "prognosis"

    return "general"


def detect_primary_disease(query: str) -> str:
    known_diseases = [
        "acute respiratory failure",
        "heart failure",
        "kawasaki disease",
        "chronic obstructive pulmonary disease",
        "acute bronchitis",
        "esophageal disease",
        "leukocytosis",
        "leukopenia",
        "tuberculosis",
        "meningitis",
        "pneumonia",
        "diabetes",
        "asthma",
        "sepsis",
        "dengue",
        "copd",
        "kawasaki",
    ]

    q = query.lower()

    for disease in sorted(known_diseases, key=len, reverse=True):
        if disease in q:
            return disease

    return ""


# ---------------- NORMALIZE / DEDUP ----------------
def normalize_for_dedup(text: Optional[str]) -> str:
    if not text:
        return ""
    text = text.lower()
    text = text.replace("­", "")   # soft hyphen
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = " ".join(text.split())
    return text.strip()


def dedup_results(results: List[Dict]) -> List[Dict]:
    cleaned = []
    seen = set()

    for r in results:
        key = (
            str(r.get("chapter_number", "")).strip().lower(),
            normalize_for_dedup(r.get("chapter_title", "")),
            normalize_for_dedup(r.get("subsection_title", "")),
            normalize_for_dedup((r.get("content") or "")[:300]),
        )

        if key in seen:
            continue

        seen.add(key)
        cleaned.append(r)

    return cleaned


# ---------------- FILTER ----------------
def build_disease_chapter_filter(
    target_chapter_numbers: List[str],
    disease_term: str = ""
):
    filters = None

    for chap in target_chapter_numbers:
        chap = str(chap).strip()
        if not chap:
            continue

        chap_filter = Filter.by_property("chapter_number").equal(chap)

        if filters is None:
            filters = chap_filter
        else:
            filters = filters | chap_filter

    disease_term = (disease_term or "").strip().lower()

    if disease_term:
        disease_filter = (
            Filter.by_property("disease_name").like(f"*{disease_term}*")
            |
            Filter.by_property("chapter_title").like(f"*{disease_term}*")
        )

        if filters is None:
            filters = disease_filter
        else:
            filters = filters | disease_filter

    return filters


# ---------------- HYBRID ----------------
def hybrid_retrieve_with_scores(
    collection,
    query: str,
    disease_term: str,
    target_chapter_numbers: List[str],
    k: int = 50,
    alpha: float = 0.5,
    query_vector: Optional[List[float]] = None,
):
    scoped_filter = build_disease_chapter_filter(target_chapter_numbers, disease_term)

    response = collection.query.hybrid(
        query=query,
        vector=query_vector,
        alpha=alpha,
        limit=k,
        filters=scoped_filter,
        return_metadata=MetadataQuery(score=True),
    )

    results = []
    for obj in response.objects:
        props = obj.properties or {}

        results.append({
            "content": props.get("content", ""),
            "book_title": props.get("book_title", ""),
            "part_title": props.get("part_title", ""),
            "section_title": props.get("section_title", ""),
            "chapter_number": props.get("chapter_number", ""),
            "chapter_title": props.get("chapter_title", ""),
            "subsection_title": props.get("subsection_title", ""),
            "normalized_subsection": props.get("normalized_subsection", ""),
            "hierarchy_path": props.get("hierarchy_path", ""),
            "page_start": props.get("page_start"),
            "page_end": props.get("page_end"),
            "content_type": props.get("content_type", ""),
            "specialty": props.get("specialty", ""),
            "age_group": props.get("age_group", ""),
            "disease_name": props.get("disease_name", ""),
            "score": getattr(obj.metadata, "score", 0),
        })

    return results


# ---------------- CLEAN ----------------
def post_filter_results(results: List[Dict]) -> List[Dict]:
    cleaned = []

    for r in results:
        if not (r.get("content") or "").strip():
            continue
        cleaned.append(r)

    return cleaned


# ---------------- DISEASE DOMINANCE ----------------
def enforce_disease_priority(results: List[Dict], disease_term: str, top_k: int = 20) -> List[Dict]:
    if not disease_term:
        return results

    disease_term = disease_term.lower().strip()

    strong = []
    others = []

    for r in results:
        text = " ".join([
            r.get("disease_name", ""),
            r.get("chapter_title", ""),
            r.get("subsection_title", ""),
            r.get("content", "")[:1200],
        ]).lower()

        if disease_term in text:
            strong.append(r)
        else:
            others.append(r)

    final = strong[:top_k]
    if len(final) < top_k:
        final.extend(others[: top_k - len(final)])

    remaining = strong[top_k:] + others[max(0, top_k - len(final)):]
    return final + remaining


# ---------------- SCORING ----------------
def preference_score(
    item: Dict,
    disease_term: str,
    intent: str,
    target_chapter_numbers: List[str]
):
    subsection = (item.get("subsection_title") or "").lower()
    norm_sub = (item.get("normalized_subsection") or "").lower()
    chapter = (item.get("chapter_title") or "").lower()
    disease_name = (item.get("disease_name") or "").lower()
    content = (item.get("content") or "").lower()[:1500]
    chapter_number = str(item.get("chapter_number", "")).lower()

    disease_term = (disease_term or "").lower().strip()
    target_set = {str(x).lower() for x in target_chapter_numbers}

    disease_score = 0
    if disease_term:
        disease_score = (
            5 * int(disease_term in disease_name) +
            4 * int(disease_term in chapter) +
            2 * int(disease_term in subsection) +
            1 * int(disease_term in content)
        )

    chapter_score = 3 * int(chapter_number in target_set)

    allowed = INTENT_TO_SUBSECTION.get(intent, set())
    subsection_score = int(norm_sub in allowed) if allowed else 0

    diagnosis_terms = [
        "diagnosis", "criteria", "clinical features", "manifestations",
        "symptoms", "signs", "evaluation", "differential"
    ]
    treatment_terms = [
        "treatment", "management", "drug", "medication", "therapy",
        "supportive care", "dose"
    ]
    investigation_terms = [
        "investigation", "test", "echocardiography", "crp", "esr",
        "platelet", "lab", "imaging"
    ]

    # extra preference / penalty by intent
    bonus = 0
    penalty = 0

    if intent == "diagnosis":
        bonus += sum(term in content for term in diagnosis_terms)
        if norm_sub in {"table", "pathobiology", "treatment"}:
            penalty += 2
    elif intent == "treatment":
        bonus += sum(term in content for term in treatment_terms)
    elif intent == "investigation":
        bonus += sum(term in content for term in investigation_terms)

    hybrid_score = item.get("score", 0)

    return (
        chapter_score,
        disease_score,
        subsection_score,
        bonus,
        -penalty,
        hybrid_score,
    )


def sort_results(
    results: List[Dict],
    disease_term: str,
    intent: str,
    target_chapter_numbers: List[str]
) -> List[Dict]:
    return sorted(
        results,
        key=lambda x: preference_score(x, disease_term, intent, target_chapter_numbers),
        reverse=True
    )


# ---------------- RERANK ----------------
def rerank_results(query: str, results: List[Dict], top_n: int = 5) -> List[Dict]:
    if not results:
        return []

    if not COHERE_API_KEY or cohere is None:
        fallback = results[:top_n]
        for r in fallback:
            r["rerank_score"] = None
        return fallback

    client = cohere.Client(COHERE_API_KEY)

    docs = []
    for r in results:
        docs.append(
            f"""
Book: {r.get('book_title')}
Part: {r.get('part_title')}
Section: {r.get('section_title')}
Chapter: {r.get('chapter_number')} - {r.get('chapter_title')}
Subsection: {r.get('subsection_title')}
Normalized Subsection: {r.get('normalized_subsection')}
Disease: {r.get('disease_name')}
Pages: {r.get('page_start')} - {r.get('page_end')}
Content Type: {r.get('content_type')}

{r.get('content')}
"""
        )

    rerank = client.rerank(
        query=query,
        documents=docs,
        top_n=min(top_n, len(docs)),
        model="rerank-english-v3.0"
    )

    reranked_results = []
    for rr in rerank.results:
        item = dict(results[rr.index])
        item["rerank_score"] = rr.relevance_score
        reranked_results.append(item)

    return reranked_results


# ---------------- PRINT ----------------
def print_results(results: List[Dict]):
    print("\n===== FINAL RESULTS =====")

    if not results:
        print("No results found.")
        return

    for i, r in enumerate(results, 1):
        print("\n" + "=" * 80)
        print(f"Rank {i}")
        print(f"Book: {r.get('book_title')}")
        print(f"Part: {r.get('part_title')}")
        print(f"Section: {r.get('section_title')}")
        print(f"Chapter: {r.get('chapter_number')} - {r.get('chapter_title')}")
        print(f"Subsection: {r.get('subsection_title')}")
        print(f"Normalized Subsection: {r.get('normalized_subsection')}")
        print(f"Hierarchy: {r.get('hierarchy_path')}")
        print(f"Pages: {r.get('page_start')} - {r.get('page_end')}")
        print(f"Content Type: {r.get('content_type')}")
        print(f"Specialty: {r.get('specialty')} | Age: {r.get('age_group')}")
        print(f"Disease Tag: {r.get('disease_name')}")
        print(f"Hybrid Score: {r.get('score')}")
        print(f"Rerank Score: {r.get('rerank_score')}")
        print("-" * 80)
        print(r.get("content", ""))


# ---------------- MAIN ----------------
def main(
    query: str,
    target_chapter_numbers: List[str],
    disease_term: Optional[str] = None
):
    query = query.strip()

    intent = detect_intent(query)
    disease = disease_term.strip().lower() if disease_term else detect_primary_disease(query)

    print("Intent:", intent)
    print("Disease:", disease)
    print("Target Chapters:", target_chapter_numbers)
    print("Alpha:", ALPHA)

    embedder = OpenAIEmbeddings(
        model=AZURE_EMBEDDING_DEPLOYMENT,
        base_url=AZURE_FOUNDRY_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        check_embedding_ctx_length=False,
    )
    query_vector = embedder.embed_query(query)

    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_CLUSTER,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
    )

    try:
        collection = client.collections.get(COLLECTION_NAME)

        results = hybrid_retrieve_with_scores(
            collection=collection,
            query=query,
            disease_term=disease,
            target_chapter_numbers=target_chapter_numbers,
            k=K,
            alpha=ALPHA,
            query_vector=query_vector,
        )
        print("Raw:", len(results))

        results = post_filter_results(results)
        results = dedup_results(results)
        print("Filtered:", len(results))

        results = sort_results(
            results=results,
            disease_term=disease,
            intent=intent,
            target_chapter_numbers=target_chapter_numbers,
        )

        results = enforce_disease_priority(results, disease)

        if USE_RERANK:
            # ask for more, dedup again, then trim
            results = rerank_results(query, results, TOP_N * 2)
            results = dedup_results(results)
            results = results[:TOP_N]
        else:
            results = dedup_results(results)
            results = results[:TOP_N]
            for r in results:
                r["rerank_score"] = None

        print_results(results)
        return results

    finally:
        client.close()


if __name__ == "__main__":
    QUERY = """Asthma diagnostic criteria episodic wheeze dyspnea cough chest tightness clinical diagnosis rules,
Asthma diagnosis criteria reversible airway obstruction spirometry bronchodilator response diagnostic features,
Asthma diagnosis in children and adults clinical features wheezing breathlessness variability and triggers,
diagnosis of asthma pulmonary function test spirometry FEV1 FVC reversibility criteria,
Asthma diagnostic approach history physical examination wheeze triggers allergens and risk factors,
clinical diagnosis of asthma symptoms nocturnal cough wheeze dyspnea chest tightness findings,
differential diagnosis of asthma COPD bronchiolitis vocal cord dysfunction,
Asthma evaluation diagnosis criteria spirometry peak flow variability and confirmation guidelines
"""
    result = main(QUERY, ["75"], disease_term="asthma")
