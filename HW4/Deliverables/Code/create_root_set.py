from elasticsearch7 import Elasticsearch

cloud_id = "7ccca25687934a25a6f3e2aa05dda5fa:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJGNhOWU5ZTIzZGFhYzRiN2FhYWIzZWE4ZDdlNDI2ZTg4JGNjYTVhNWViMzg5ZDQ0NzlhMDU2NTNjMWFiMDMzNGE0"
es = Elasticsearch(cloud_id=cloud_id, http_auth=('elastic', 'PlPWA4aQmC4PnzDZKre6VC0J'))
index_name = 'climate-change'

query = "climate change"
res_es_search = es.search(index=index_name, body={
    "query": {
        "match": {
            "text":{
            "query": query}
        }
    },
    "fields": ["docno"],
    "size": 1000
})

f = open("./root_set.txt", "w")
for hit in res_es_search['hits']['hits']:
    f.write(hit['fields']['docno'][0] + '\n')
f.close()
