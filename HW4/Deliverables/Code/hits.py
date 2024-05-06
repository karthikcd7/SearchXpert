from elasticsearch7 import Elasticsearch
import random

cloud_id = "7ccca25687934a25a6f3e2aa05dda5fa:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJGNhOWU5ZTIzZGFhYzRiN2FhYWIzZWE4ZDdlNDI2ZTg4JGNjYTVhNWViMzg5ZDQ0NzlhMDU2NTNjMWFiMDMzNGE0"
es = Elasticsearch(cloud_id=cloud_id, http_auth=('elastic', 'PlPWA4aQmC4PnzDZKre6VC0J'))
index_name = 'climate-change'

def create_root_set():
    query = "climate change"
    res_es_search = es.search(index=index_name, body={
        "query": {
            "match": {
                "text":{
                    "query": query
                }
            }
        },
        "fields": ["docno"],
        "size": 1000
    })

    root_set = []
    for hit in res_es_search['hits']['hits']:
        root_set.append(hit['fields']['docno'][0])
    return root_set

def set_index():
    index = {}
    for page in root_set:
        index[page] = es.get(index=index_name, id=page)
    return index

def expand_root_set(root_set, d=200):
    base_set = set()
    for page in root_set:
        index = es.get(index=index_name, id=page)
        base_set.update(index['_source']["outlinks"])
        inlinks = index['_source']["inlinks"]
        if len(inlinks) <= d:
            base_set.update(inlinks)
        else:
            base_set.update(random.sample(inlinks, d))
    return base_set

def compute_hits(index, base_set, max_iterations=5, tol=1e-6):
    hubs = {}
    authorities = {}
    for page in base_set:
        hubs[page] = 1
        authorities[page] = 1
    
    for _ in range(max_iterations):
        print("Iteration", _)
        new_authorities = {}
        new_hubs = {}
        
        # Update authority scores and hub scores
        for page in base_set:
            try:
                if page not in index:
                    index[page] = es.get(index=index_name, id=page)
                new_authorities[page] = sum(hubs[p] for p in index[page]['_source']["inlinks"])
                new_hubs[page] = sum(authorities[p] for p in index[page]['_source']["outlinks"])
            except:
                new_authorities[page] = 0
                new_hubs[page] = 0
        print("Scores computed")
        # Normalize scores
        auth_sum = sum(new_authorities.values())
        for page, score in new_authorities.items():
            if auth_sum == 0:
                new_authorities[page] = 0
            else:
                new_authorities[page] = score / auth_sum

        hub_sum = sum(new_hubs.values())
        for page, score in new_hubs.items():
            if hub_sum == 0:
                new_hubs[page] = 0
            else:
                new_hubs[page] = score / hub_sum
        print("Authorities normalized")

        # Check for convergence
        auth_diff = sum(abs(new_authorities[page] - authorities[page]) for page in base_set)
        hub_diff = sum(abs(new_hubs[page] - hubs[page]) for page in base_set)
        if auth_diff < tol and hub_diff < tol:
            break
        print("Differences computed")
        
        authorities = new_authorities
        hubs = new_hubs
    
    return authorities, hubs

def write_top_pages(authorities, hubs):
    sorted_authorities = sorted(authorities.items(), key=lambda x: x[1], reverse=True)
    sorted_hubs = sorted(hubs.items(), key=lambda x: x[1], reverse=True)
    
    with open(f"../Results/top_authorities.txt", 'w') as auth_file:
        for page, score in sorted_authorities[:500]:
            auth_file.write(f"{page}\t{score}\n")
    
    with open(f"../Results/top_hubs.txt", 'w') as hub_file:
        for page, score in sorted_hubs[:500]:
            hub_file.write(f"{page}\t{score}\n")

root_set = create_root_set()
print(len(root_set), "root pages found")
base_set = expand_root_set(root_set)
print(len(base_set), "base pages found")
index = set_index()
print(len(index), "pages indexed")
authorities, hubs = compute_hits(index, base_set)
print("HITS computation complete")
write_top_pages(authorities, hubs)
print("Top pages written to file")
