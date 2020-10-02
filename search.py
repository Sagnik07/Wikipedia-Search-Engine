import sys
from collections import defaultdict
import Stemmer
import timeit
import re
from bisect import bisect
from math import log10
import json

stemmer = Stemmer.Stemmer('english')

total_no_of_docs = 0

#document title mapping file
doc_to_title_map = {}
doc_to_title_file_name = "DOC_ID_TO_TITLE.txt"
try:
    fp = open(doc_to_title_file_name, "r")
    for line in fp:
        seperator = line.index(" ")
        doc_ID = line[0:seperator].strip()
        doc_title = line[seperator:].strip()
        doc_to_title_map[doc_ID] = doc_title
        total_no_of_docs += 1
    fp.close()
except:
    print("Document title mapping file missing")
    sys.exit(1)

#word position mapping file
word_pos_dict = {}
try:
    with open("index_folder/WORD_TO_POSITION.json", "r") as posfile: 
        word_pos_dict = json.load(posfile)
    posfile.close()
except:
    print("Word position mapping file missing")
    sys.exit(1)

#stopwords file
stop_words = set()
try:
    fp = open("stopwords.txt","r")
    for line in fp:
        stop_words.add(line.strip())
    fp.close()
except:
    print("Stopwords file missing")
    sys.exit(1)

#secondary index file
secondary_index = list()
try:
    f = open("index_folder/secondary_index.txt","r")
    for line in f:
        secondary_index.append(line.split()[0])
    f.close()
except:
    print("Secondary index file missing")
    sys.exit(1)

#weight of fields
field_weight = {}
field_weight["t"] = 1000
field_weight["i"] = 50
field_weight["r"] = 50
field_weight["l"] = 50
field_weight["c"] = 50
field_weight["b"] = 1


def normal_query(search_string, k):
    global field_weight, output_file

    search_words = search_string.split()

    wordsToSearch = list()
    for word in search_words:
        word = re.sub(r'[^\x00-\x7F]+','', word)
        word = word.lower().strip()
        if word not in stop_words:
            word = stemmer.stemWord(word)
        if word.isalpha() and len(word)>=3 and word not in stop_words:
            wordsToSearch.append(word)


    tf_idf_map = defaultdict(int)
    secondary_index_length = len(secondary_index)
    for word in wordsToSearch:
        position = bisect(secondary_index, word)
        if position-1 >= 0 and secondary_index[position-1] == word:
            if position-1 != 0:
                position -= 1
            if position+1 == secondary_index_length and secondary_index[position] == word:
                position += 1

        primaryFile = "index_folder/index" + str(position) + ".txt"

        file = open(primaryFile,"r")
        word_to_be_searched = word_pos_dict.get(word)
        if word_to_be_searched == None:
            continue
        file.seek(word_to_be_searched)

        word_line = file.readline()
        
        postings_list = word_line.split(":")[1].split(",")
        current_no_of_docs = len(postings_list)
        idf = log10(total_no_of_docs/current_no_of_docs)

        for entry in postings_list:
            doc_ID, doc_entry = entry.split("-")
            field_freq = doc_entry.split("|")
            tf = 0
            for key in field_freq:
                field = key[0]
                frequency = key[1:]
                tf += int(frequency) * int(field_weight[field])
            
            tf_idf_map[doc_ID] += float(log10(1+tf)) * float(idf)



    doc_score_map = sorted(tf_idf_map.items(), key=lambda item: item[1], reverse=True)[0:k]

    for i in doc_score_map:
        doc_ID, score = i
        # print(doc_to_title_map[doc_ID])
        output_file.write(str(doc_ID) + ", " + str(doc_to_title_map[doc_ID]) + "\n")
    

def field_query(query, k):
    global field_weight, output_file

    tf_idf_map = defaultdict(int)
    # print("field query : ", query)
    secondary_index_length = len(secondary_index)
    for word, current_field in query:
        position = bisect(secondary_index, word)
        if position-1 >= 0 and secondary_index[position-1] == word:
            if position-1 != 0:
                position -= 1
            if position+1 == secondary_index_length and secondary_index[position] == word:
                position += 1

        primaryFile = "index_folder/index" + str(position) + ".txt"

        file = open(primaryFile,"r")
        word_to_be_searched = word_pos_dict.get(word)
        if word_to_be_searched == None:
            continue
        file.seek(word_to_be_searched)
        word_line = file.readline()

        postings_list = word_line.split(":")[1].split(",")
        new_postings_list = []
        for i in postings_list:
            if current_field in i:
                new_postings_list.append(i)

        if len(new_postings_list) == 0:
            new_postings_list = postings_list 

        current_no_of_docs = len(new_postings_list)
        idf = log10(total_no_of_docs/current_no_of_docs)
        
        for d in new_postings_list:
            doc_ID, doc_entry = d.split("-")
            field_freq = doc_entry.split("|")
            tf = 0
            for key in field_freq:
                field = key[0]
                frequency = key[1:]
                tf += int(frequency) * int(field_weight[field])
            
            tf_idf_map[doc_ID] += float(log10(1+tf)) * float(idf)

    doc_score_map = sorted(tf_idf_map.items(), key=lambda item: item[1], reverse=True)[0:k]

    for i in doc_score_map:
        doc_ID, score = i
        # print(doc_to_title_map[doc_ID])
        output_file.write(str(doc_ID) + ", " + str(doc_to_title_map[doc_ID]) + "\n")



if len(sys.argv) != 2:
	print("Invalid arguments")
	sys.exit(1)


inp_file_name = sys.argv[1]


try:
    inp_file = open(inp_file_name, "r")
except:
    print("Queries file missing")
    sys.exit(1)

output_file = open("2019201003_queries_op.txt", "w")

fields = ["t", "i", "b", "r", "l", "c"]

for queries in inp_file:
    queries = queries.strip()
    queries = queries.split(",")
    k = int(queries[0].strip())
    search_string = queries[1].strip()
    # print(k, " ", search_string)

    field_flag = 0
    try:
        field_flag = search_string.index(":")
    except:
        pass

    start_time = timeit.default_timer()
    if field_flag == 0:
        normal_query(search_string, k)
    
    else:
        fields_list = []
        i = 0
        for field in fields:
            field_queries = str(field) + ":"
            try:
                field_index = search_string.index(field_queries)
                fields_list.append(field_index)
            except:
                pass

        fields_list.append(len(search_string)+1)

        parsed_query = []
        for i in range(len(fields_list)-1):
            query = search_string[fields_list[i]:fields_list[i+1]-1]
            query.strip()
            query = query.split(":")
            field = query[0]
            if field not in fields:
                print("No such field", field)
                continue
            words = query[1].split(" ")
            for word in words:
                word = re.sub(r'[^\x00-\x7F]+','', word)
                word = word.lower().strip()
                if word not in stop_words:
                    word = stemmer.stemWord(word)
                if word.isalpha() and len(word)>=3 and word not in stop_words:
                    parsed_query.append((word,field))

        field_query(parsed_query, k)

    stop_time = timeit.default_timer()
    time_req = stop_time - start_time
    output_file.write(str(time_req) + ", " + str(time_req/k) + "\n\n")

output_file.close()
print("DONE!!")