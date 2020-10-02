import json
import sys
import os
import timeit
import glob
from heapq import heapify, heappush, heappop

def secondary_indexing():
	global secondary_index, merged_index_folder

	index_file_name = merged_index_folder + "secondary_index.txt"
	fps = open(index_file_name,"w")
	for word in sorted(secondary_index):
		fps.write(str(word) + " " + str(secondary_index[word]) + "\n")
	fps.close()

def primary_indexing(inverted_index):
	global index_file_no, word_pos_dict, indexed_tokens, secondary_index, merged_index_folder
	
	index_file_name = merged_index_folder + "index" + str(index_file_no) + ".txt"
	fp = open(index_file_name,"w")
	indexed_tokens += len(inverted_index)
	
	flag = 0
	for word in sorted(inverted_index):
		if flag == 0:
			secondary_index[word] = index_file_no
			flag = 1
		word_pos_dict[word] = fp.tell()
		fp.write(str(word) + ":" + inverted_index[word] + "\n")
	fp.close()
	index_file_no = index_file_no + 1

def merge_files():
	global limit, inverted_index_files

	file_parsed = []
	heap_file = []
	file_row = {}
	postings = {}
	fp = {}
	total_files = len(inverted_index_files)

	for i in range(total_files):
		file_parsed.append(0)
		try:
			fp[i] = open(inverted_index_files[i],"r")
		except:
			print("Index file missing")
		file_row[i] = fp[i].readline()
		postings[i] = file_row[i].strip().split(":")
		word = postings[i][0]
		if word not in heap_file:
			heappush(heap_file, word)

	parsed_files = 0
	

	count = 0
	inverted_index = {}
	while parsed_files < total_files:
		count += 1
		word = heappop(heap_file)
		for i in range(total_files):
			if file_parsed[i] == 0 and postings[i][0] == word:
				if word in inverted_index:
					inverted_index[word] += "," + postings[i][1]
				else:
					inverted_index[word] = postings[i][1]

				file_row[i] = fp[i].readline().strip()

				if file_row[i]:
					postings[i] = file_row[i].split(":")
					current_word = postings[i][0]
					if current_word not in heap_file:
						heappush(heap_file, current_word)
				else:
					parsed_files += 1
					file_parsed[i] = 1
					fp[i].close()
					#os.remove(inverted_index_files[i])

				if count == limit:
					primary_indexing(inverted_index)
					inverted_index = {}
					count = 0

	primary_indexing(inverted_index)
	secondary_indexing()



inverted_index_files = glob.glob("./inverted_index/*")
merged_index_folder = "index_folder/"
index_file_no = 1
secondary_index = {}
limit = 75000

indexed_tokens = 0
word_pos_dict = {}

try:
    os.mkdir(merged_index_folder)
except FileExistsError:
    print("Directory already exists!")

start_time = timeit.default_timer()
merge_files()
stop_time = timeit.default_timer()

with open("./index_folder/WORD_TO_POSITION.json", "w") as outfile: 
    json.dump(word_pos_dict, outfile) 

outfile.close()

stats_file = open("stats.txt", "w")
stats_file.write(str(index_file_no-1) + "\n")
stats_file.write(str(indexed_tokens))
stats_file.close()

print("Index merging time : ")
seconds = stop_time - start_time
minutes = float(seconds)/float(60)
hours = float(minutes)/float(60)
print(hours," hours")
print(minutes," minutes")
print(seconds," seconds")
