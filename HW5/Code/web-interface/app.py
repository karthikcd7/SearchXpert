from flask import Flask, render_template, request, jsonify
from collections import defaultdict

app = Flask(__name__)
urls = defaultdict(list)
with open('../data/urls.txt', 'r') as f:
    links = f.read().split('\n')
    for link in links[:-1]:
        urls[link[:6]].append(link[8:])

topics = {
    "150501": "difference between weather and climate",
    "150502": "sea rise predictions",
    "150503": "human impact on climate",
    "150504": "The Impact of Climate Change on Biodiversity"
}
doc_ids = {}
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', links=urls, topics=topics)

@app.route('/update_rating', methods=['POST'])
def update_rating():
    index = int(request.form['index'])
    rating = int(request.form['rating'])
    key = request.form['key']
    print(key, index, urls[key][index%200-1], rating)
    doc_ids[index] = urls[key][index%200-1]
    with open('../data/ratings.txt', 'a') as f:
        f.write(f'{key} Karthik_ChintamaniDileep {urls[key][index%200-1]} {rating}\n')
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
