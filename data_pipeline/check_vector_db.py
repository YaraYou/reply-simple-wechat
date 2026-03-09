from __future__ import annotations

from pathlib import Path

import chromadb

from app.config import settings


def main():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    collection = client.get_collection("chat_history")

    print(f"chroma_path={settings.chroma_path}")
    print(f"collection=chat_history")
    print(f"count={collection.count()}")

    rows = collection.get(limit=5)
    docs = rows.get("documents") or []
    print(f"sample_docs={len(docs)}")
    for i, doc in enumerate(docs, 1):
        text = (doc or "").replace("\n", "\\n")
        print(f"--- doc{i} ---")
        print(text[:200])

    examples_file = Path(settings.multi_turn_examples_path)
    if examples_file.exists():
        stat = examples_file.stat()
        print(
            f"examples_file={examples_file} size={stat.st_size} "
            f"mtime={examples_file.stat().st_mtime}"
        )
    else:
        print(f"examples_file={examples_file} missing")


if __name__ == "__main__":
    main()
