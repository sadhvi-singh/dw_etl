# -*- coding: utf-8 -*-
"""pyvespa_search.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1glnc75og5gSIDCKveWwj3bA5GHFj6LZ9
"""

#!pip install vespa -q

#!pip install pyvespa -q

import pandas as pd
from vespa.application import Vespa
from vespa.io import VespaResponse, VespaQueryResponse


def display_hits_as_df(response: VespaQueryResponse, fields) -> pd.DataFrame:
    records = []
    for hit in response.hits:
        record = {}
        for field in fields:
            record[field] = hit["fields"][field]
        records.append(record)
    return pd.DataFrame(records)

def keyword_search(app, search_query):
    query = {
        "yql": "select * from sources * where userQuery() limit 5",
        "query": search_query,
        "ranking": "bm25",
    }
    response = app.query(query)
    return display_hits_as_df(response, ["doc_id", "title"])

def semantic_search(app, query):
    query = {
        "yql": "select * from sources * where ({targetHits:100}nearestNeighbor(embedding,e)) limit 5",
        "query": query,
        "ranking": "semantic",
        "input.query(e)": "embed(@query)"
    }
    response = app.query(query)
    return display_hits_as_df(response, ["doc_id", "title"])

def get_embedding(doc_id):
    query = {
        "yql" : f"select doc_id, title, text, embedding from content.doc where doc_id contains '{doc_id}'",
        "hits": 1
    }
    result = app.query(query)

    if result.hits:
        return result.hits[0]  # Return the first hit
    else:
        print(f"No results found for doc_id: {doc_id}")
        return None  # Return None if no hits are found

def query_books_by_embedding(embedding_vector):
    query = {
        'hits': 5,
        'yql': 'select * from content.doc where ({targetHits:5}nearestNeighbor(embedding, user_embedding))',
        'ranking.features.query(user_embedding)': str(embedding_vector),
        'ranking.profile': 'recommendation'
    }
    return app.query(query)


# Replace with the host and port of your local Vespa instance
app = Vespa(url="http://localhost", port=8082)

query = "Vampire Academy"

# Keyword search
print("\nPerforming Keyword Search...")
df = keyword_search(app, query)
print(df.head())

# Semantic search
print("\nPerforming Semantic Search...")
df = semantic_search(app, query)
print(df.head())

# Get embedding and perform the embedding-based search
emb = get_embedding("345627.Vampire_Academy")
if emb is not None and "fields" in emb and "embedding" in emb["fields"]:
    print("\nPerforming Search Based on Embedding...")
    results = query_books_by_embedding(emb["fields"]["embedding"])
    df = display_hits_as_df(results, ["doc_id", "title", "text"])
    print(df.head())
else:
    print("Embedding not found for doc_id '345627'.")