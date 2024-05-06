from flask import Flask, render_template, request
from elasticsearch import Elasticsearch

app = Flask(__name__)

cloud_id = "ce055d24579b469dbf9b169eb4f05957:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQ4MDQwNzc3MmNkZDg0ZTA3YWVlNmJlNjY1ZGJlZjU2MCQ5OGUwNDVkMmFhNDI0MzQ3OWYzZGY4YmE1M2FjNWE1Yw=="

es = Elasticsearch(cloud_id=cloud_id, http_auth=("elastic", "Li0EioDUXKdbapQUBSbU4q8Y"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return render_template('index.html', error='Please enter a query.')

    # Search Elasticsearch index
    result = es.search(index='climate-change', body={'query': {'match': {'text': query}}})
    hits = result['hits']['hits']
    
    # Extract relevant information
    search_results = []
    for hit in hits:
        docno = hit['_id']
        title = hit['_source']['title']
        search_results.append({'docno': docno, 'title': title})

    return render_template('index.html', query=query, search_results=search_results)

if __name__ == '__main__':
    app.run(debug=True)
