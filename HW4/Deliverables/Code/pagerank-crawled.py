import numpy as np
from elasticsearch7 import Elasticsearch
cloud_id = "7ccca25687934a25a6f3e2aa05dda5fa:dXMtZWFzdDQuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJGNhOWU5ZTIzZGFhYzRiN2FhYWIzZWE4ZDdlNDI2ZTg4JGNjYTVhNWViMzg5ZDQ0NzlhMDU2NTNjMWFiMDMzNGE0"
es = Elasticsearch(cloud_id=cloud_id, http_auth=('elastic', 'PlPWA4aQmC4PnzDZKre6VC0J'))

index_name = 'climate-change'
def get_allPages_inlinks_outlinks_sink():
    inlinks = {}
    outlinks = {}
    all_pages = []
    sink = []

    res = es.search(index=index_name, body={"query": {"match_all": {}}, 'size': 1000}, scroll='1m')
    scroll_id = res['_scroll_id']
    hits = res['hits']['hits']
    while hits:
        for hit in hits:
            page = hit['_source']['docno']
            all_pages.append(page)
            if 'outlinks' not in hit['_source']:
                outlinks[page] = 1
            else:
                outlinks[page] = len(hit['_source']['outlinks'])
            if 'inlinks' not in hit['_source']:
                inlinks[page] = []
            else:
                inlinks[page] = hit['_source']['inlinks']
        res = es.scroll(scroll_id=scroll_id, scroll='1m')
        scroll_id = res['_scroll_id']
        hits = res['hits']['hits']

    for page in outlinks:
        if outlinks[page] == 0:
            sink.append(page)
    
    return all_pages, inlinks, outlinks, sink

def get_perplexity(PR):
    pr_values = np.array(list(PR.values()))
    pr_values = pr_values[pr_values > 0]
    entropy = -np.sum(pr_values * np.log2(pr_values))
    perplexity = 2 ** entropy
    return perplexity

def compute_pagerank(all_pages, inlinks, outlinks, sinks, damping_factor=0.85, max_iterations=500, threshold=1e-6):
    
    N = len(all_pages)
    pagerank = {page: 1 / N for page in inlinks}
    
    old_perplexity = get_perplexity(pagerank)
    
    for i in range(max_iterations):
        new_pagerank = {}
        sink_pr = 0
        
        for page in sinks:
            sink_pr += pagerank[page]
        
        for page in inlinks:
            new_pagerank[page] = (1 - damping_factor) / N + damping_factor * sink_pr / N
            
            for in_page in inlinks[page]:
                if in_page not in pagerank or in_page not in outlinks:
                    continue
                new_pagerank[page] += damping_factor * pagerank[in_page] / outlinks[in_page]
        for page in inlinks:
            pagerank[page] = new_pagerank[page]
        
        new_perplexity = get_perplexity(pagerank)
        if abs(old_perplexity - new_perplexity) < threshold:
            break
        
        old_perplexity = new_perplexity
    
    return pagerank

P, M, L, S = get_allPages_inlinks_outlinks_sink()
pagerank_scores = compute_pagerank(P, M, L, S)
sorted_pagerank = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
output = open('../Results/pagerank-crawled_output.txt', 'w')
for page, score in sorted_pagerank[:500]:
    print(f"{page} {score} {L[page]} {len(M[page])}")
    output.write(f"{page} {score} {L[page]} {len(M[page])}\n")
output.close()
