"""Merge Index on Elasticsearch cloud"""
import os
import re
from elasticsearch import Elasticsearch
import json
cloud_id = "7ccca25687934a25a6f3e2aa05dda5fa:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJGNhOWU5ZTIzZGFhYzRiN2FhYWIzZWE4ZDdlNDI2ZTg4JGNjYTVhNWViMzg5ZDQ0NzlhMDU2NTNjMWFiMDMzNGE0"
es = Elasticsearch(request_timeout=10000, cloud_id=cloud_id, http_auth=('elastic', 'PlPWA4aQmC4PnzDZKre6VC0J'))
print(es.ping())
index_name = "climate-change"



def create_index(index_name):
    # create index
    configurations = {
        "settings" : {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "stopped": {
                        "type": "custom",
                        "tokenizer": "standard"
                    }
                }
            }
        },
        "mappings": {
            "properties": {
                "content": {
                    "type": "text",
                    "fielddata": True,
                    "analyzer": "stopped",
                    "index_options": "positions"
                }
            }
        }
    }

    es.indices.create(index=index_name, body=configurations)
        

def add_to_index(folder):
    i=0
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        with open(file_path, 'rb') as f:
            content = f.read().decode('iso-8859-1')
        doc_regex = r'<DOC>(.*?)</DOC>'
        for doc in re.findall(doc_regex, content, re.S):
            docno = re.search(r'<DOCNO>(.*?)</DOCNO>', doc).group(1).strip()
            title = re.search(r'<TITLE>(.*?)</TITLE>', doc, re.DOTALL).group(1).strip()
            text = re.findall(r'<TEXT>(.*?)</TEXT>', doc, re.S)
            outlinks = []
            if docno in outlinks_map:
                outlinks = outlinks_map[docno]
            inlinks = []
            if docno in inlinks_map:
                inlinks = inlinks_map[docno]

            doc_source = {
                "docno": docno,
                "title": title,
                "text": text,
                "outlinks": outlinks,
                "inlinks": inlinks,
                "author": "Karthik Chintamani Dileep"
            }
            try:
                es.index(index=index_name, id=docno, body=doc_source)
            except Exception as e:
                print(e)
            i+=1
        print(f"Indexed until:", i)



path = '/Users/karthik/Documents/NEU/4th Sem/IR/Assignments/hw3-karthikcd7/Results/'

with open(path + 'outlinks.json', 'r') as f:
    outlinks_map = json.load(f)
with open(path + 'inlinks.json', 'r') as f:
    inlinks_map = json.load(f)
create_index(index_name)
add_to_index(path+'webpages-content/')


