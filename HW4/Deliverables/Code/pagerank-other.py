import numpy as np

def get_allPages_inlinks_outlinks_sink(file_path):
    inlinks = {}
    outlinks = {}
    all_pages = []
    sink = []
    
    with open(file_path, 'r') as f:
        for line in f:
            tokens = line.strip().split()
            page = tokens[0]
            all_pages.append(page)
            outlinks[page] = 0
            inlinks[page] = list(set(tokens[1:]))

    for pages in inlinks.values():
        for page in pages:
            if page in outlinks:
                outlinks[page] += 1
            else:
                outlinks[page] = 1
                inlinks[page] = []

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
                new_pagerank[page] += damping_factor * pagerank[in_page] / outlinks[in_page]
        for page in inlinks:
            pagerank[page] = new_pagerank[page]
        
        new_perplexity = get_perplexity(pagerank)
        if abs(old_perplexity - new_perplexity) < threshold:
            break
        
        old_perplexity = new_perplexity
    
    return pagerank

P, M, L, S = get_allPages_inlinks_outlinks_sink('../../Resources/wt2g_inlinks.txt')
pagerank_scores = compute_pagerank(P, M, L, S)
sorted_pagerank = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
output = open('../Results/pagerank-wt2g_output.txt', 'w')
for page, score in sorted_pagerank[:500]:
    print(f"{page} {score} {L[page]} {len(M[page])}")
    output.write(f"{page} {score} {L[page]} {len(M[page])}\n")
output.close()
