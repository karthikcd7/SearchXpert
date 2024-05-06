import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.corpus import stopwords
import re
import string
from collections import defaultdict
from elasticsearch7 import Elasticsearch
from elasticsearch7.client import IndicesClient
import time
import math
import os
import pickle

qrel_path = 'data/qrel/'

qrel_docs = {}
with open('data/qrel/qrels.adhoc.51-100.AP89.txt', 'r') as f:
    for line in f.readlines():
        line = line.replace("\n", "")
        query_id, _, doc_id, rel = line.split(" ")
        if query_id in qrel_docs:
            qrel_docs[query_id][doc_id] = rel
        else:
            qrel_docs[query_id] = {}
            qrel_docs[query_id][doc_id] = rel

other_docs = {}
files = os.listdir(qrel_path)
files.remove('qrels.adhoc.51-100.AP89.txt')
model_scores = {}
for f in files:
    file_path = qrel_path + f
    with open(file_path, 'r') as file:
        data = file.read().split('\n')[:-1]
        key = f.split('.')[0]
        model_scores[key] = defaultdict(dict)
        for each in data:
            q_id, _, doc_id, rank, score, _  = each.split()
            model_scores[key][q_id][doc_id] = score

query_doc = {}
model_scores = {}
models = ['es_scores', 'okapi_bm25', 'okapi_tf', 'tfidf', 'unigram_lml', 'unigram_lmjm']
for model in models:
    files = os.listdir(f'data/scores/{model}/')
    for f in files:
        file_path = f'data/scores/{model}/' + f
        q_id = f.split('.')[0].split('_')[-1]
        with open(file_path, 'rb') as file:
            data_map = pickle.load(file)
            key = model
            if key == 'es_scores':
                key = 'es_built_in'
            if key not in model_scores:
                model_scores[key] = defaultdict(dict)
            else:
                model_scores[key][q_id] = data_map


        # with open(file_path, 'r') as file:
        #     data = file.read().split('\n')[:-1]
        #     key = f.split('.')[0]
        #     if key == 'es_scores':
        #         key = 'es_built_in'
        #     if key not in model_scores:
        #         model_scores[key] = defaultdict(dict)
        #     for each in data:
        #         q_id, _, doc_id, rank, score, _  = each.split()
        #         model_scores[key][q_id][doc_id] = score
all_scores = {}
for model in models: 
    files = os.listdir(f'data/scores/{model}/')
    all_scores[model] = defaultdict(dict)
    for file in files:
        q_id = file.split('.')[0].split('_')[-1]
        with open (f'data/scores/{model}/{file}', 'rb') as f:
            all_scores[model][q_id] = pickle.load(f)
    



queries = ['54', '56', '57', '58', '59', '60', '61', '62', '63', '64', '68', '71', '77', '80', '85', '87', '89', '91', '93', '94', '95', '97', '98', '99', '100']
df = pd.DataFrame(columns=['q-id_doc-id', 'es_score', 'okapi_bm25_score', 'okapi_tf_score', 'tf_idf_score', 'unigram_lml_score', 'unigram_lmjm_score', 'label'])
count = 0

for q_id in qrel_docs.keys():
    non_rel_docs = set()
    if q_id not in queries:
        continue
    for doc_id in qrel_docs[q_id].keys():
        row = {
            'q-id_doc-id': q_id + '_' + doc_id,
            'es_score': model_scores['es_built_in'][q_id].get(doc_id, all_scores['es_scores'][q_id].get(doc_id, 0)),
            'okapi_bm25_score': model_scores['okapi_bm25'][q_id].get(doc_id, all_scores['okapi_bm25'][q_id].get(doc_id, 0)),
            'okapi_tf_score': model_scores['okapi_tf'][q_id].get(doc_id, all_scores['okapi_tf'][q_id].get(doc_id, 0)),
            'tf_idf_score': model_scores['tfidf'][q_id].get(doc_id, all_scores['tfidf'][q_id].get(doc_id, 0)),
            'unigram_lml_score': model_scores['unigram_lml'][q_id].get(doc_id, all_scores['unigram_lml'][q_id].get(doc_id, 0)),
            'unigram_lmjm_score': model_scores['unigram_lmjm'][q_id].get(doc_id, all_scores['unigram_lmjm'][q_id].get(doc_id, 0)),
            'label': qrel_docs[q_id].get(doc_id, 0)
        }
        if int(row['es_score']) == 0 or int(row['okapi_bm25_score']) == 0 or int(row['okapi_tf_score']) == 0 or int(row['tf_idf_score']) == 0:
            continue
        if int(row['label']) == 0:
            non_rel_docs.add(doc_id)
        df.loc[count] = row
        count+=1
    print(f'Non Relevant docs complete for {q_id}:{len(non_rel_docs)}')
    iterations = 0
    while len(non_rel_docs) < 1000:
        for model in model_scores:
            for doc_id in model_scores[model][q_id]:
                if doc_id in non_rel_docs:
                    continue
                iterations += 1
                row = {
                    'q-id_doc-id': q_id + '_' + doc_id,
                    'es_score': model_scores['es_built_in'][q_id].get(doc_id, all_scores['es_scores'][q_id].get(doc_id, 0)),
                    'okapi_bm25_score': model_scores['okapi_bm25'][q_id].get(doc_id, all_scores['okapi_bm25'][q_id].get(doc_id, 0)),
                    'okapi_tf_score': model_scores['okapi_tf'][q_id].get(doc_id, all_scores['okapi_tf'][q_id].get(doc_id, 0)),
                    'tf_idf_score': model_scores['tfidf'][q_id].get(doc_id, all_scores['tfidf'][q_id].get(doc_id, 0)),
                    'unigram_lml_score': model_scores['unigram_lml'][q_id].get(doc_id, all_scores['unigram_lml'][q_id].get(doc_id, 0)),
                    'unigram_lmjm_score': model_scores['unigram_lmjm'][q_id].get(doc_id, all_scores['unigram_lmjm'][q_id].get(doc_id, 0)),
                    'label': 0
                }
                non_rel_docs.add(doc_id)
                df.loc[count] = row
                count+=1
                if len(non_rel_docs) >= 1000:
                    break
                if iterations > 2000:
                    break
            if len(non_rel_docs) >= 1000:
                    break
            if iterations > 2000:
                break
        if len(non_rel_docs) >= 1000:
            break
        if iterations > 2000:
            break


df.to_csv('data/qrel.csv', index=False)



