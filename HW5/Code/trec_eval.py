import sys
import matplotlib.pyplot as plt
# Usage
if len(sys.argv) < 3 or len(sys.argv) > 4:
    sys.exit("Usage:  trec_eval [-q] <qrel_file> <trec_file>\n\n")

# Get names of qrel and trec files; check for -q option.
if len(sys.argv) == 4:
    sys.argv.pop(1)  # Remove -q.
    print_all_queries = True
else:
    print_all_queries = False

qrel_file = sys.argv[1]
trec_file = sys.argv[2]

# Process qrel file first.
with open(qrel_file, 'r') as qrel:
    data = qrel.read().split()

# Initialize data structures
qrel_dict = {}
num_rel = {}

# Now take the values from the data array (four at a time) and put them in a data structure.
dummy = 0
while data:
    topic, dummy, doc_id, rel, *data = data
    qrel_dict.setdefault(topic, {})[doc_id] = int(rel)
    num_rel[topic] = num_rel.get(topic, 0) + int(rel)

# Process the trec file.
with open(trec_file, 'r') as trec:
    data = trec.read().split()

# Initialize data structures
trec_dict = {}

# Process the trec_file data
while data:
    topic, dummy, doc_id, dummy, score, dummy, *data = data
    trec_dict.setdefault(topic, {})[doc_id] = float(score)

def print_eval_results(qid, ret, rel, rel_ret, *args):
    print("\nQueryid (Num):    {:>5}".format(qid))
    print("Total number of documents over all queries")
    print("    Retrieved:    {:>5}".format(ret))
    print("    Relevant:     {:>5}".format(rel))
    print("    Rel_ret:      {:>5}".format(rel_ret))
    print("Interpolated Recall - Precision Averages:")
    print("    at 0.00       {:.4f}".format(args[0]))
    print("    at 0.10       {:.4f}".format(args[1]))
    print("    at 0.20       {:.4f}".format(args[2]))
    print("    at 0.30       {:.4f}".format(args[3]))
    print("    at 0.40       {:.4f}".format(args[4]))
    print("    at 0.50       {:.4f}".format(args[5]))
    print("    at 0.60       {:.4f}".format(args[6]))
    print("    at 0.70       {:.4f}".format(args[7]))
    print("    at 0.80       {:.4f}".format(args[8]))
    print("    at 0.90       {:.4f}".format(args[9]))
    print("    at 1.00       {:.4f}".format(args[10]))
    print("Average precision (non-interpolated) for all rel docs(averaged over queries)")
    print("                  {:.4f}".format(args[11]))
    print("Precision:")
    print("  At    5 docs:   {:.4f}".format(args[12]))
    print("  At   10 docs:   {:.4f}".format(args[13]))
    print("  At   15 docs:   {:.4f}".format(args[14]))
    print("  At   20 docs:   {:.4f}".format(args[15]))
    print("  At   30 docs:   {:.4f}".format(args[16]))
    print("  At  100 docs:   {:.4f}".format(args[17]))
    print("  At  200 docs:   {:.4f}".format(args[18]))
    print("  At  500 docs:   {:.4f}".format(args[19]))
    print("  At 1000 docs:   {:.4f}".format(args[20]))
    print("R-Precision (precision after R (= num_rel for a query) docs retrieved):")
    print("    Exact:        {:.4f}".format(args[21]))


# Initialize some arrays.
recalls = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
cutoffs = [5, 10, 15, 20, 30, 100, 200, 500, 1000]

# Now let's process the data from trec_file to get results.
num_topics = 0
tot_num_ret = 0
tot_num_rel = 0
tot_num_rel_ret = 0
sum_avg_prec = 0
sum_r_prec = 0
sum_prec_at_cutoffs = [0] * len(cutoffs)
sum_prec_at_recalls = [0] * len(recalls)
prec_dict = {}
rec_dict = {}
for topic in sorted(trec_dict.keys()):  # Process topics in order.
    if not num_rel.get(topic):
        continue

    num_topics += 1
    href = trec_dict[topic]

    prec_list = [0] * 1001  # New list of precisions.
    rec_list = [0] * 1001  # Recall list.

    num_ret = 0  # Initialize number retrieved.
    num_rel_ret = 0  # Initialize number relevant retrieved.
    sum_prec = 0  # Initialize sum precision.

    # Now sort doc IDs based on scores and calculate stats.
    for doc_id, score in sorted(href.items(), key=lambda x: (x[1], x[0]), reverse=True):
        num_ret += 1
        rel = qrel_dict[topic].get(doc_id, 0)  # Doc's relevance.

        if rel:
            sum_prec += rel * (1 + num_rel_ret) / num_ret
            num_rel_ret += rel

        prec_list[num_ret] = num_rel_ret / num_ret
        rec_list[num_ret] = num_rel_ret / num_rel[topic]

        if num_ret >= 1000:
            break

    avg_prec = sum_prec / num_rel[topic]

    # Fill out the remainder of the precision/recall lists, if necessary.
    final_recall = num_rel_ret / num_rel[topic]
    for i in range(num_ret + 1, 1001):
        prec_list[i] = num_rel_ret / i
        rec_list[i] = final_recall

    # Now calculate precision at document cutoff levels and R-precision.
    prec_at_cutoffs = [prec_list[cutoff] for cutoff in cutoffs]

    if num_rel[topic] > num_ret:
        r_prec = num_rel_ret / num_rel[topic]
    else:
        int_num_rel = int(num_rel[topic])  # Integer part.
        frac_num_rel = num_rel[topic] - int_num_rel  # Fractional part.

        if frac_num_rel > 0:
            r_prec = (1 - frac_num_rel) * prec_list[int_num_rel] + frac_num_rel * prec_list[int_num_rel + 1]
        else:
            r_prec = prec_list[int_num_rel]

    max_prec = 0
    for i in range(1000, 0, -1):
        if prec_list[i] > max_prec:
            max_prec = prec_list[i]
        else:
            prec_list[i] = max_prec

    # Finally, calculate precision at recall levels.
    prec_at_recalls = []
    i = 1
    for recall in recalls:
        while i <= 1000 and rec_list[i] < recall:
            i += 1
        if i <= 1000:
            prec_at_recalls.append(prec_list[i])
        else:
            prec_at_recalls.append(0)

    # Now update running sums for overall stats.
    tot_num_ret += num_ret
    tot_num_rel += num_rel[topic]
    tot_num_rel_ret += num_rel_ret

    for i, cutoff in enumerate(cutoffs):
        sum_prec_at_cutoffs[i] += prec_at_cutoffs[i]

    for i, recall in enumerate(recalls):
        sum_prec_at_recalls[i] += prec_at_recalls[i]

    sum_avg_prec += avg_prec
    sum_r_prec += r_prec

    prec_dict[topic] = prec_list
    rec_dict[topic] = rec_list
    # Print stats on a per query basis if requested.
    if print_all_queries:
        print_eval_results(topic, num_ret, num_rel[topic], num_rel_ret,
                           *prec_at_recalls, avg_prec, *prec_at_cutoffs, r_prec)

# Now calculate summary stats.
print(f"Error due to {num_topics}")
avg_prec_at_cutoffs = [sum_prec / num_topics for sum_prec in sum_prec_at_cutoffs]
avg_prec_at_recalls = [sum_prec / num_topics for sum_prec in sum_prec_at_recalls]
mean_avg_prec = sum_avg_prec / num_topics
avg_r_prec = sum_r_prec / num_topics

print_eval_results(num_topics, tot_num_ret, tot_num_rel, tot_num_rel_ret,
                   *avg_prec_at_recalls, mean_avg_prec, *avg_prec_at_cutoffs,
                   avg_r_prec)
for topic, prec_list in prec_dict.items():
    rec_list = rec_dict[topic]
    plt.plot(rec_list, prec_list, label=f'Query {topic}')

plt.xlabel('Recall')
plt.ylabel('Precision')
plt.title('Precision-Recall Curves')
plt.legend()
plt.show()