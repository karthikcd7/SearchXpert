from elasticsearch7 import Elasticsearch
cloud_id = "ce055d24579b469dbf9b169eb4f05957:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQ4MDQwNzc3MmNkZDg0ZTA3YWVlNmJlNjY1ZGJlZjU2MCQ5OGUwNDVkMmFhNDI0MzQ3OWYzZGY4YmE1M2FjNWE1Yw=="
es = Elasticsearch(cloud_id=cloud_id, http_auth=("elastic", "Li0EioDUXKdbapQUBSbU4q8Y"))
index_name = 'climate-change'

f = open("./data/urls.txt", "w")
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
        f.write(str(150501+i) + ": " + hit['fields']['docno'][0]+ "\n")
f.close()
