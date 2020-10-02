import sys
import Stemmer

def search(index_file, orig_word, search_word, field_flag, field = ""):
  # print(search_word, " ", field)
  field_mapping = {"t":"title", "b":"body", "i":"infobox", "r":"references", "l":"links", "c":"category"}
  postings = []
  f = open(index_file, "r")
  for line in f:
    line = line.strip()
    entry = line.split(':')
    if search_word == entry[0]:
      print("\nPostings list of", orig_word, " ", line)
      dict1 = entry[1]
      dict1 = dict1.split(",")
      if field_flag == 0:
        for docs in dict1:
          postings.append(docs.split('-')[0])
      else:
        for docs in dict1:
          field_index = -1
          try:
            field_index = docs.index(field)
          except:
            pass
          if field_index != -1:
            postings.append(docs.split('-')[0])
      break
  
  print()
  if len(postings) > 0:
    if field_flag == 0:
      print(orig_word, "present in documents :",postings)
    else:
      print(orig_word, "present in ", field_mapping[field], " of documents :",postings)
  else:
    if field_flag == 0:
      print(orig_word, "not present")
    else:
      print(orig_word, "not present in field", field_mapping[field])

# search_string = "World Cup i:2019 c:Cricket"
# search_string = "World Cup"
# search_string = "Hogwarts"
# search_string = "Sachin Ramesh Tendulkar"

if len(sys.argv) < 3:
	print("Invalid arguments")
	sys.exit(1)

#search_string = ""
#for i in range(2, len(sys.argv)):
#  search_string += sys.argv[i] + " "

#search_string = search_string.strip()
index_file = sys.argv[1]
search_string = sys.argv[2]
index_file = index_file + "inverted_index.txt"

stemmer = Stemmer.Stemmer('english')

field_flag = 0
try:
  field_flag = search_string.index(":")
except:
  pass

if field_flag == 0:
  search_string = search_string.strip()
  words = search_string.split()
  for word in words:
    stemmed_word = word.lower()
    stemmed_word = stemmer.stemWord(stemmed_word)
    search(index_file, word, stemmed_word, field_flag)

else:
  # print("field_flag: ", field_flag)
  fields = ["t", "i", "b", "r", "l", "c"]
  fields_list = []
  i = 0
  for field in fields:
    field_query = str(field) + ":"
    try:
      field_index = search_string.index(field_query)
      fields_list.append(field_index)
    except:
      pass

  # print(fields_list)
  fields_list.append(len(search_string)+1)

  if fields_list[0] != 0:
    words = search_string[0:fields_list[0]]
    words = words.strip()
    words = words.split()
    for word in words:
      stemmed_word = word.lower()
      stemmed_word = stemmer.stemWord(stemmed_word)
      search(index_file, word, stemmed_word, 0)

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
      stemmed_word = word.lower()
      stemmed_word = stemmer.stemWord(stemmed_word)
      search(index_file, word, stemmed_word, field_flag, field)
