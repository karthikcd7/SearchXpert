from elasticsearch7 import Elasticsearch
from collections import defaultdict
cloud_id = "ce055d24579b469dbf9b169eb4f05957:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQ4MDQwNzc3MmNkZDg0ZTA3YWVlNmJlNjY1ZGJlZjU2MCQ5OGUwNDVkMmFhNDI0MzQ3OWYzZGY4YmE1M2FjNWE1Yw=="
es = Elasticsearch(cloud_id=cloud_id, http_auth=("elastic", "Li0EioDUXKdbapQUBSbU4q8Y"))
index_name = 'climate-change'

score = {}

query = ["difference between weather and climate", "sea rise predictions", "human impact on climate", "The Impact of Climate Change on Biodiversity"]
for i, q in enumerate(query):
    res_es_search = es.search(index=index_name, body={
        "query": {
            "match": {
                "text":{
                "query": q}
            }
        },
        "fields": ["docno"],
        "size": 200
    })
    for hit in res_es_search['hits']['hits']:
        score[hit['_id']] = format(hit['_score'], '.10f')
with open("../Results/qrel_karthik.txt", "w") as f1, open("../Results/ratings.txt", "r") as f2:
    data = f2.read().split('\n')[:-1]
    for line in data:    
        qid, name, docid, rating = line.split()
        f1.write(f"{qid} {name} {docid} {rating} {score[docid]} Exp\n")


