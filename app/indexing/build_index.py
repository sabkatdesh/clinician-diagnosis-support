import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import tiktoken
import weaviate
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.document_loaders import PyMuPDFLoader, PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.init import Auth
from weaviate.util import generate_uuid5

load_dotenv()

from app.config import (
    WEAVIATE_CLUSTER,
    WEAVIATE_API_KEY,
    AZURE_EMBEDDING_ENDPOINT,
    AZURE_OPENAI_API_KEY,
    AZURE_EMBEDDING_DEPLOYMENT,
    DOC_PATH,
    COLLECTION_NAME,
)

# text-embedding-3-small accepts at most 8192 tokens per input.
# Only the text sent to the embedder is shortened; the stored content stays complete.
_ENC = tiktoken.get_encoding("cl100k_base")
MAX_EMBED_TOKENS = 8000


def truncate_for_embedding(text: str) -> str:
    toks = _ENC.encode(text, disallowed_special=())
    if len(toks) <= MAX_EMBED_TOKENS:
        return text
    print(f"  [truncated for embedding: {len(toks)} tokens]")
    return _ENC.decode(toks[:MAX_EMBED_TOKENS])

# =========================================================
# CONFIG
# =========================================================
TOP_HEADER_LINES = 12
MIN_TEXT_LEN = 60
ENABLE_HELPER_CHILD_CHUNKS = False
HELPER_CHILD_CHUNK_CHARS = 2200
HELPER_CHILD_CHUNK_OVERLAP = 250

# Only trust these subsection labels strongly.
CANONICAL_SUBSECTION_MAP: Dict[str, List[str]] = {
    "definition": ["definition", "definitions"],
    "epidemiology": ["epidemiology"],
    "etiology": ["etiology", "aetiology", "causes"],
    "pathophysiology": ["pathophysiology", "pathogenesis", "mechanism", "mechanisms"],
    "pathobiology": ["pathobiology"],
    "clinical_manifestations": [
        "clinical manifestations",
        "clinical features",
        "presentation",
        "presentations",
        "signs and symptoms",
        "symptoms",
        "history",
        "history and examination",
    ],
    "physical_examination": ["physical examination", "thoracic examination"],
    "diagnosis": [
        "diagnosis",
        "diagnostic evaluation",
        "diagnostic approach",
        "laboratory findings",
        "pulmonary function findings",
        "differential diagnosis",
    ],
    "treatment": [
        "treatment",
        "management",
        "therapy",
        "specific management",
        "drug treatment",
        "supportive management",
        "asthma medications",
    ],
    "prognosis": ["prognosis"],
    "prevention": ["prevention", "preventive measures", "prophylaxis"],
    "complications": ["complications", "adverse effects", "sequelae"],
    "references": ["general references", "references"],
}

SKIP_EXACT_SUBSECTION_TITLES = {
    "contents",
    "index",
    "chapter",
}

SPECIALTY_KEYWORDS = {
    "respiratory": ["asthma", "copd", "lung", "bronch", "pulmonary", "airway", "pleura"],
    "cardiology": ["heart", "cardiac", "arrhythmia", "coronary", "myocard"],
    "gastroenterology": ["liver", "hepatic", "pancrea", "bowel", "intestin", "abdomen"],
    "neurology": ["brain", "stroke", "seizure", "neurolog", "cranial", "cns"],
    "infectious_disease": ["infection", "viral", "bacterial", "fungal", "sepsis", "tuberculosis"],
    "rheumatology": ["arthritis", "vasculitis", "lupus", "autoimmune"],
    "oncology": ["cancer", "tumor", "lymphoma", "leukemia", "malignan"],
    "pediatrics": ["child", "children", "pediatric", "infant", "neonate", "adolescent"],
}

AGE_GROUP_KEYWORDS = {
    "neonate": ["neonate", "newborn"],
    "infant": ["infant"],
    "child": ["child", "children", "pediatric"],
    "adolescent": ["adolescent", "teen"],
    "adult": ["adult"],
    "older_adult": ["older adult", "geriatric", "elderly"],
}


# =========================================================
# DATA CLASSES
# =========================================================
@dataclass
class PageRecord:
    page_num: int
    raw_text: str
    clean_text: str
    source: str
    book_title: str
    header_lines: List[str] = field(default_factory=list)
    chapter_number: str = ""
    chapter_title: str = ""
    header_text: str = ""


@dataclass
class ChapterBlock:
    book_title: str
    source: str
    chapter_number: str
    chapter_title: str
    page_start: int
    page_end: int
    pages: List[PageRecord] = field(default_factory=list)

    @property
    def disease_name(self) -> str:
        return self.chapter_title.strip()

    @property
    def full_text(self) -> str:
        texts = [p.clean_text for p in self.pages if p.clean_text]
        return "\n\n".join(texts).strip()


@dataclass
class SectionChunk:
    content: str
    book_title: str
    source: str
    chapter_number: str
    chapter_title: str
    subsection_title: str
    normalized_subsection: str
    hierarchy_path: str
    content_type: str
    page_start: int
    page_end: int
    disease_name: str
    specialty: str
    age_group: str
    header_text: str = ""
    helper_parent_key: str = ""


# =========================================================
# ENV / CLIENT
# =========================================================
def require_env() -> None:
    missing = []
    for key, value in {
        "WEAVIATE_CLUSTER": WEAVIATE_CLUSTER,
        "WEAVIATE_API_KEY": WEAVIATE_API_KEY,
        "AZURE_EMBEDDING_ENDPOINT": AZURE_EMBEDDING_ENDPOINT,
        "AZURE_OPENAI_API_KEY": AZURE_OPENAI_API_KEY,
        "AZURE_EMBEDDING_DEPLOYMENT": AZURE_EMBEDDING_DEPLOYMENT,
        "DOC_PATH": DOC_PATH,
    }.items():
        if not value:
            missing.append(key)

    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")


def connect_client():
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=WEAVIATE_CLUSTER,
        auth_credentials=Auth.api_key(WEAVIATE_API_KEY),
        skip_init_checks=True,
    )
    print("Connected:", client.is_ready())
    return client


# =========================================================
# COLLECTION
# =========================================================
def create_collection_if_missing(client, name: str):
    if client.collections.exists(name):
        print(f"Collection '{name}' already exists.")
        return

    client.collections.create(
        name=name,
        vector_config=Configure.Vectors.self_provided(),
        properties=[
            Property(name="content", data_type=DataType.TEXT),
            Property(name="source", data_type=DataType.TEXT),
            Property(name="book_title", data_type=DataType.TEXT),
            Property(name="doc_id", data_type=DataType.TEXT),
            Property(name="chunk_id", data_type=DataType.INT),
            Property(name="chapter_number", data_type=DataType.TEXT),
            Property(name="chapter_title", data_type=DataType.TEXT),
            Property(name="subsection_title", data_type=DataType.TEXT),
            Property(name="normalized_subsection", data_type=DataType.TEXT),
            Property(name="hierarchy_path", data_type=DataType.TEXT),
            Property(name="page_start", data_type=DataType.INT),
            Property(name="page_end", data_type=DataType.INT),
            Property(name="content_type", data_type=DataType.TEXT),
            Property(name="disease_name", data_type=DataType.TEXT),
            Property(name="specialty", data_type=DataType.TEXT),
            Property(name="age_group", data_type=DataType.TEXT),
            Property(name="header_text", data_type=DataType.TEXT),
            Property(name="helper_parent_key", data_type=DataType.TEXT),
        ],
    )
    print(f"Created collection '{name}'.")


# =========================================================
# PDF LOAD
# =========================================================
def load_pdf_pages(pdf_path: str) -> List[Document]:
    errors = []

    try:
        print("Trying PyMuPDFLoader...")
        loader = PyMuPDFLoader(pdf_path)
        pages = loader.load()
        if pages:
            print(f"Loaded with PyMuPDFLoader: {len(pages)} pages")
            return pages
    except Exception as e:
        errors.append(f"PyMuPDFLoader failed: {repr(e)}")

    try:
        print("Trying PyPDFLoader fallback...")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        if pages:
            print(f"Loaded with PyPDFLoader: {len(pages)} pages")
            return pages
    except Exception as e:
        errors.append(f"PyPDFLoader failed: {repr(e)}")

    raise RuntimeError("Failed to load PDF.\n" + "\n".join(errors))


# =========================================================
# TEXT CLEANING
# =========================================================
def safe_title_from_path(path: str) -> str:
    base = os.path.basename(path)
    stem, _ = os.path.splitext(base)
    return stem.strip()


def normalize_whitespace(text: str) -> str:
    text = text.replace(" ", " ")
    text = text.replace("\t", " ")
    text = text.replace("ﬁ", "fi").replace("ﬂ", "fl")
    text = text.replace("—", "-").replace("–", "-")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_page_text(text: str) -> str:
    text = normalize_whitespace(text)
    text = re.sub(r"(?m)^\s*Downloaded from .*$", "", text)
    text = re.sub(r"(?m)^\s*Copyright .*?$", "", text)
    text = re.sub(r"(?m)^\s*AccessMedicine.*?$", "", text)
    text = re.sub(r"(?m)^\s*\d+\s*$", "", text)
    text = normalize_whitespace(text)
    return text


def split_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.split("\n") if ln.strip()]


def normalize_heading(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s\-:]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def mostly_uppercase(line: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", line)
    if len(letters) < 4:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return upper / max(len(letters), 1) >= 0.75


# =========================================================
# PAGE -> CHAPTER DETECTION
# =========================================================
def extract_header_lines(clean_text: str, top_n: int = TOP_HEADER_LINES) -> List[str]:
    lines = split_lines(clean_text)
    return lines[:top_n]


def extract_chapter_from_header_lines(lines: List[str]) -> Tuple[str, str]:
    if not lines:
        return "", ""

    joined = " ".join(lines[:4])

    # Case 1: CHAPTER 75 ASTHMA
    m = re.search(r"\bCHAPTER\s+(\d{1,4})\s+([A-Z][A-Z0-9 ,/&\-\(\)']{2,80})\b", joined)
    if m:
        chap_num = m.group(1).strip()
        chap_title = m.group(2).strip(" -:")
        if is_valid_chapter_title(chap_title):
            return chap_num, title_case_safe(chap_title)

    # Case 2: CHAPTER 75 / ASTHMA on next line
    for i, line in enumerate(lines[:6]):
        m = re.match(r"^\s*CHAPTER\s+(\d{1,4})\s*$", line, flags=re.I)
        if m and i + 1 < len(lines):
            chap_num = m.group(1).strip()
            chap_title = lines[i + 1].strip()
            if is_valid_chapter_title(chap_title):
                return chap_num, title_case_safe(chap_title)

    # Case 3: CHAPTER 75 ASTHMA as separate tokens with odd spacing
    for i, line in enumerate(lines[:6]):
        m = re.match(r"^\s*CHAPTER\s+(\d{1,4})\b(.*)$", line, flags=re.I)
        if m:
            chap_num = m.group(1).strip()
            tail = m.group(2).strip()
            if tail and is_valid_chapter_title(tail):
                return chap_num, title_case_safe(tail)

            if i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if is_valid_chapter_title(nxt):
                    return chap_num, title_case_safe(nxt)

    return "", ""


def is_valid_chapter_title(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if len(t) > 80:
        return False
    if len(t.split()) > 10:
        return False
    if re.search(r"https?://", t, flags=re.I):
        return False
    if t.endswith("."):
        return False
    if re.search(r"\)\s*,", t):
        return False
    if re.search(r"^\W+$", t):
        return False

    letters = re.sub(r"[^A-Za-z]", "", t)
    if len(letters) < 3:
        return False

    # allow upper / title case / mixed medical labels
    return True


def title_case_safe(text: str) -> str:
    t = text.strip()
    if mostly_uppercase(t):
        return t.title()
    return t


def build_page_records(pages: List[Document], source_path: str) -> List[PageRecord]:
    book_title = safe_title_from_path(source_path)
    records: List[PageRecord] = []

    last_chapter_number = ""
    last_chapter_title = ""

    for page_idx, page in enumerate(pages, start=1):
        raw_text = page.page_content or ""
        clean_text = clean_page_text(raw_text)
        header_lines = extract_header_lines(clean_text)
        chap_num, chap_title = extract_chapter_from_header_lines(header_lines)

        # inherit chapter if this page header doesn't repeat it
        if chap_num and chap_title:
            last_chapter_number = chap_num
            last_chapter_title = chap_title
        else:
            chap_num = last_chapter_number
            chap_title = last_chapter_title

        rec = PageRecord(
            page_num=page_idx,
            raw_text=raw_text,
            clean_text=clean_text,
            source=source_path,
            book_title=book_title,
            header_lines=header_lines,
            chapter_number=chap_num,
            chapter_title=chap_title,
            header_text=" | ".join(header_lines[:4]),
        )
        records.append(rec)

    return records


# =========================================================
# PAGE -> CHAPTER BLOCKS
# =========================================================
def build_chapter_blocks(page_records: List[PageRecord]) -> List[ChapterBlock]:
    blocks: List[ChapterBlock] = []
    current: Optional[ChapterBlock] = None

    for page in page_records:
        if not page.chapter_number or not page.chapter_title:
            continue

        if current is None:
            current = ChapterBlock(
                book_title=page.book_title,
                source=page.source,
                chapter_number=page.chapter_number,
                chapter_title=page.chapter_title,
                page_start=page.page_num,
                page_end=page.page_num,
                pages=[page],
            )
            continue

        same_chapter = (
            current.chapter_number == page.chapter_number
            and normalize_heading(current.chapter_title) == normalize_heading(page.chapter_title)
            and page.page_num == current.page_end + 1
        )

        if same_chapter:
            current.pages.append(page)
            current.page_end = page.page_num
        else:
            blocks.append(current)
            current = ChapterBlock(
                book_title=page.book_title,
                source=page.source,
                chapter_number=page.chapter_number,
                chapter_title=page.chapter_title,
                page_start=page.page_num,
                page_end=page.page_num,
                pages=[page],
            )

    if current is not None:
        blocks.append(current)

    return blocks


# =========================================================
# CHAPTER -> SUBSECTION DETECTION
# =========================================================
def normalize_subsection_label(title: str) -> str:
    nt = normalize_heading(title)

    for canonical, variants in CANONICAL_SUBSECTION_MAP.items():
        for v in variants:
            if normalize_heading(v) == nt:
                return canonical

    if nt.startswith("figure"):
        return "figure"
    if nt.startswith("table"):
        return "table"

    return ""


def detect_table_heading(line: str) -> Optional[str]:
    if re.match(r"^\s*(TABLE|Table)\s+\d+[A-Za-z0-9\-\.:]*", line):
        return line.strip()
    return None


def detect_figure_heading(line: str) -> Optional[str]:
    if re.match(r"^\s*(FIGURE|Figure|Fig\.?)\s+\d+[A-Za-z0-9\-\.:]*", line):
        return line.strip()
    return None


def is_candidate_subsection_heading(line: str) -> bool:
    t = line.strip()
    if not t:
        return False
    if len(t) > 80:
        return False
    if t.endswith("."):
        return False
    if re.search(r"https?://", t, flags=re.I):
        return False

    nt = normalize_heading(t)
    if nt in SKIP_EXACT_SUBSECTION_TITLES:
        return False

    if detect_table_heading(t) or detect_figure_heading(t):
        return True

    if normalize_subsection_label(t):
        return True

    # strong uppercase short heading
    if mostly_uppercase(t) and len(t.split()) <= 6:
        return True

    return False


def page_body_lines_without_header(page: PageRecord) -> List[str]:
    lines = split_lines(page.clean_text)

    # remove top header lines
    header_norms = {normalize_heading(x) for x in page.header_lines[:TOP_HEADER_LINES]}
    trimmed = []
    skip_budget = len(page.header_lines[:TOP_HEADER_LINES])

    for line in lines:
        nl = normalize_heading(line)
        if skip_budget > 0 and nl in header_norms:
            skip_budget -= 1
            continue
        trimmed.append(line)

    return trimmed


def infer_content_type_from_title(subsection_title: str) -> str:
    ns = normalize_subsection_label(subsection_title)
    if ns == "figure":
        return "figure"
    if ns == "table":
        return "table"
    return "text"


def make_hierarchy_path(chapter_number: str, chapter_title: str, subsection_title: str) -> str:
    base = f"Chapter {chapter_number}: {chapter_title}".strip()
    if subsection_title:
        return f"{base} > {subsection_title}"
    return base


def split_large_text_for_helpers(text: str, max_chars: int, overlap: int) -> List[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    pieces = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        piece = text[start:end]

        if end < len(text):
            last_break = max(
                piece.rfind("\n\n"),
                piece.rfind(". "),
                piece.rfind("; "),
                piece.rfind(", "),
            )
            if last_break > int(max_chars * 0.6):
                end = start + last_break + 1
                piece = text[start:end]

        pieces.append(piece.strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)

    return [p for p in pieces if p]


def infer_specialty(text: str) -> str:
    low = text.lower()
    scores = {
        spec: sum(1 for kw in kws if kw in low)
        for spec, kws in SPECIALTY_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general_medicine"


def infer_age_group(text: str) -> str:
    low = text.lower()
    scores = {
        age: sum(1 for kw in kws if kw in low)
        for age, kws in AGE_GROUP_KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "all"


def chapter_to_section_chunks(block: ChapterBlock) -> List[SectionChunk]:
    chunks: List[SectionChunk] = []

    current_title = ""
    current_norm = ""
    current_type = "text"
    current_lines: List[str] = []
    current_page_start: Optional[int] = None
    current_page_end: Optional[int] = None

    def flush_current():
        nonlocal current_title, current_norm, current_type
        nonlocal current_lines, current_page_start, current_page_end

        text = normalize_whitespace("\n".join(current_lines))
        if len(text) < MIN_TEXT_LEN:
            current_lines = []
            current_page_start = None
            current_page_end = None
            return

        subsection_title = current_title or "Chapter Overview"
        normalized_subsection = current_norm
        hierarchy_path = make_hierarchy_path(
            block.chapter_number,
            block.chapter_title,
            subsection_title,
        )

        meta_text = " ".join([
            block.chapter_title,
            subsection_title,
            text[:2500],
        ])

        chunk = SectionChunk(
            content=text,
            book_title=block.book_title,
            source=block.source,
            chapter_number=block.chapter_number,
            chapter_title=block.chapter_title,
            subsection_title=subsection_title,
            normalized_subsection=normalized_subsection,
            hierarchy_path=hierarchy_path,
            content_type=current_type,
            page_start=current_page_start or block.page_start,
            page_end=current_page_end or block.page_end,
            disease_name=block.disease_name,
            specialty=infer_specialty(meta_text),
            age_group=infer_age_group(meta_text),
            header_text=f"CHAPTER {block.chapter_number} {block.chapter_title}",
        )
        chunks.append(chunk)

        if ENABLE_HELPER_CHILD_CHUNKS and current_type == "text":
            helper_parent_key = f"{hierarchy_path}||{chunk.page_start}-{chunk.page_end}"
            parts = split_large_text_for_helpers(
                chunk.content,
                max_chars=HELPER_CHILD_CHUNK_CHARS,
                overlap=HELPER_CHILD_CHUNK_OVERLAP,
            )
            if len(parts) > 1:
                for idx, part in enumerate(parts):
                    chunks.append(
                        SectionChunk(
                            content=part,
                            book_title=chunk.book_title,
                            source=chunk.source,
                            chapter_number=chunk.chapter_number,
                            chapter_title=chunk.chapter_title,
                            subsection_title=f"{chunk.subsection_title} [helper {idx + 1}]",
                            normalized_subsection=chunk.normalized_subsection,
                            hierarchy_path=chunk.hierarchy_path,
                            content_type="helper_text",
                            page_start=chunk.page_start,
                            page_end=chunk.page_end,
                            disease_name=chunk.disease_name,
                            specialty=chunk.specialty,
                            age_group=chunk.age_group,
                            header_text=chunk.header_text,
                            helper_parent_key=helper_parent_key,
                        )
                    )

        current_lines = []
        current_page_start = None
        current_page_end = None

    for page in block.pages:
        body_lines = page_body_lines_without_header(page)

        for line in body_lines:
            if not line.strip():
                continue

            if is_candidate_subsection_heading(line):
                new_norm = normalize_subsection_label(line)
                new_type = infer_content_type_from_title(line)

                # Start a new subsection
                if current_lines:
                    flush_current()

                current_title = line.strip()
                current_norm = new_norm
                current_type = new_type
                current_page_start = page.page_num
                current_page_end = page.page_num

                # keep heading line in figure/table chunks
                if new_type in {"figure", "table"}:
                    current_lines = [line]
                else:
                    current_lines = []
                continue

            if current_page_start is None:
                current_page_start = page.page_num
            current_page_end = page.page_num
            current_lines.append(line)

    if current_lines:
        flush_current()

    return chunks


# =========================================================
# CHUNKS -> DOCUMENTS
# =========================================================
def section_chunks_to_documents(chunks: List[SectionChunk]) -> List[Document]:
    docs: List[Document] = []

    for chunk in chunks:
        content = chunk.content.strip()
        if not content or len(content) < MIN_TEXT_LEN:
            continue

        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": chunk.source,
                    "book_title": chunk.book_title,
                    "chapter_number": chunk.chapter_number,
                    "chapter_title": chunk.chapter_title,
                    "subsection_title": chunk.subsection_title,
                    "normalized_subsection": chunk.normalized_subsection,
                    "hierarchy_path": chunk.hierarchy_path,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "content_type": chunk.content_type,
                    "disease_name": chunk.disease_name,
                    "specialty": chunk.specialty,
                    "age_group": chunk.age_group,
                    "header_text": chunk.header_text,
                    "helper_parent_key": chunk.helper_parent_key,
                },
            )
        )

    return docs


# =========================================================
# DEDUP / INSERT
# =========================================================
def get_existing_keys(collection):
    keys = set()
    for obj in collection.iterator(return_properties=["doc_id", "chunk_id"]):
        props = obj.properties or {}
        keys.add(f"{props.get('doc_id')}||{props.get('chunk_id')}")
    return keys


# =========================================================
# DEBUG PRINTS
# =========================================================
def print_page_header_preview(page_records: List[PageRecord], limit: int = 20):
    print("\n===== PAGE HEADER PREVIEW =====")
    for rec in page_records[:limit]:
        print("-" * 100)
        print("Page:", rec.page_num)
        print("Header lines:", rec.header_lines[:4])
        print("Detected chapter:", rec.chapter_number, "-", rec.chapter_title)


def print_chapter_block_preview(blocks: List[ChapterBlock], limit: int = 20):
    print("\n===== CHAPTER BLOCK PREVIEW =====")
    for block in blocks[:limit]:
        print("-" * 100)
        print(
            f"Chapter {block.chapter_number}: {block.chapter_title} | "
            f"Pages {block.page_start}-{block.page_end} | "
            f"Count pages: {len(block.pages)}"
        )


def print_chunk_preview(docs: List[Document], limit: int = 20):
    print("\n===== FINAL CHUNK PREVIEW =====")
    for i, d in enumerate(docs[:limit], start=1):
        print("=" * 100)
        print("Chunk:", i)
        print("Book:", d.metadata.get("book_title"))
        print("Chapter:", d.metadata.get("chapter_number"), "-", d.metadata.get("chapter_title"))
        print("Subsection:", d.metadata.get("subsection_title"))
        print("Normalized:", d.metadata.get("normalized_subsection"))
        print("Hierarchy:", d.metadata.get("hierarchy_path"))
        print("Pages:", d.metadata.get("page_start"), "-", d.metadata.get("page_end"))
        print("Type:", d.metadata.get("content_type"))
        print("Disease:", d.metadata.get("disease_name"))
        print("Specialty:", d.metadata.get("specialty"))
        print("Age:", d.metadata.get("age_group"))
        print("Preview:", d.page_content)


# =========================================================
# MAIN
# =========================================================
def main() -> None:
    require_env()
    client = connect_client()

    try:
        # Collection already uses self-provided vectors: keep it and resume.
        # Chunks already stored are skipped below (existing keys).

        create_collection_if_missing(client, COLLECTION_NAME)
        collection = client.collections.get(COLLECTION_NAME)

        pages = load_pdf_pages(DOC_PATH)
        print("Pages loaded:", len(pages))

        page_records = build_page_records(pages, DOC_PATH)
        print("Page records built:", len(page_records))
        print_page_header_preview(page_records, limit=15)

        chapter_blocks = build_chapter_blocks(page_records)
        print("Chapter blocks built:", len(chapter_blocks))
        print_chapter_block_preview(chapter_blocks, limit=20)

        all_chunks: List[SectionChunk] = []
        for block in chapter_blocks:
            chunks = chapter_to_section_chunks(block)
            all_chunks.extend(chunks)

        print("Section chunks built:", len(all_chunks))

        final_docs = section_chunks_to_documents(all_chunks)
        print("Final docs ready for indexing:", len(final_docs))
        print_chunk_preview(final_docs[19:39], limit=20)

        doc_id = generate_uuid5(DOC_PATH)
        for i, d in enumerate(final_docs):
            d.metadata["doc_id"] = doc_id
            d.metadata["chunk_id"] = i

        chunk_uuids = [
            generate_uuid5(
                f"{DOC_PATH}||{i}||{d.metadata.get('hierarchy_path', '')}||{d.page_content[:1000]}"
            )
            for i, d in enumerate(final_docs)
        ]

        existing_keys = get_existing_keys(collection)
        print("Existing keys:", len(existing_keys))

        new_docs = []
        new_ids = []
        for d, uid in zip(final_docs, chunk_uuids):
            key = f"{d.metadata['doc_id']}||{d.metadata['chunk_id']}"
            if key not in existing_keys:
                new_docs.append(d)
                new_ids.append(uid)

        print("New docs:", len(new_docs))
        print("Skipped docs:", len(final_docs) - len(new_docs))

        embedder = OpenAIEmbeddings(
            model=AZURE_EMBEDDING_DEPLOYMENT,
            base_url=AZURE_EMBEDDING_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            check_embedding_ctx_length=False,
            max_retries=6,
        )

        BATCH_SIZE = 25

        if new_docs:
            with collection.batch.fixed_size(batch_size=BATCH_SIZE) as batch:
                for i in range(0, len(new_docs), BATCH_SIZE):
                    batch_slice = new_docs[i:i + BATCH_SIZE]
                    ids_slice = new_ids[i:i + BATCH_SIZE]

                    print(f"Embedding batch {i} -> {i + len(batch_slice)}")
                    vectors = embedder.embed_documents([truncate_for_embedding(d.page_content) for d in batch_slice])
                    print("Inserting batch...")

                    for doc, uid, vec in zip(batch_slice, ids_slice, vectors):
                        props = {"content": doc.page_content, **doc.metadata}
                        batch.add_object(properties=props, uuid=uid, vector=vec)

                    print(f"Batch {i} inserted.")

            failed = collection.batch.failed_objects
            if failed:
                first = getattr(failed[0], "message", failed[0])
                raise RuntimeError(f"{len(failed)} objects failed to insert. First error: {first}")
        else:
            print("No new docs to insert.")

        count = collection.aggregate.over_all(total_count=True).total_count
        print(f"Collection '{COLLECTION_NAME}' object count: {count}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
