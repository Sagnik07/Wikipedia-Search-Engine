import xml.sax
import re
import Stemmer
import timeit
import sys
import os
import glob
import json

regex1 = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',re.DOTALL)
regex2 = re.compile(r'{\|(.*?)\|}',re.DOTALL)
regex3 = re.compile(r'{{v?cite(.*?)}}',re.DOTALL)
regex4 = re.compile(r'[-.,:;_?()"/\']',re.DOTALL)
regex5 = re.compile(r'\[\[file:(.*?)\]\]',re.DOTALL)
regex6 = re.compile(r"[~`!@#$%-^*+{\[}\]\|\\<>/?]",re.DOTALL)

regex7 = re.compile(r'{{(.*?)}}',re.DOTALL)
regex8 = re.compile(r'<(.*?)>',re.DOTALL)

stemmer = Stemmer.Stemmer('english')


def create_index(header, word_list, docID):
  global total_number_of_tokens, inverted_index

  for word in word_list:
    word = re.sub(r'[^\x00-\x7F]+','', word)
    word = word.strip()
    total_number_of_tokens = total_number_of_tokens + 1
    if len(word) <= 2 or word in stop_words:
      continue
    if word.isalnum() or word.isdigit():
      word = stemmer.stemWord(word)
      if word in stop_words:
        continue
      if word not in inverted_index:
        inverted_index[word] = {}
      if docID not in inverted_index[word]:
        inverted_index[word][docID] = {}
      if header not in inverted_index[word][docID]:
        inverted_index[word][docID][header] = 1
      else:
        inverted_index[word][docID][header] += 1



def create_index_file(inverted_index_file_path):
  global inverted_index

  index_file = open(inverted_index_file_path, "w")
  for word,value in sorted(inverted_index.items()):
      entry =str(word)+":"
      for docID,val in sorted(value.items()):
          entry += str(docID) + "-"
          for header,v in val.items():
              entry = entry + str(header) + str(v) + "|"
          entry = entry[:-1]+","
      index_file.write(entry[:-1]+"\n")
  index_file.close()


def create_index_stat_file(inverted_index_stat_path):
  global total_number_of_tokens, indexed_tokens
  
  f = open(inverted_index_stat_path, "w")
  f.write(str(total_number_of_tokens) + "\n")
  f.write(str(indexed_tokens))
  f.close()


def process_title(title, docID):
  title = title.lower()
  title = regex1.sub(' ', title)
  title = regex2.sub(' ', title)
  title = regex3.sub(' ', title)
  title = regex4.sub(' ', title)
  title = regex5.sub(' ', title)
  title = regex6.sub(' ', title)
  title = regex8.sub(' ', title)
  title = title.split()
#   print("\n\nDoc ID : ", docID, " Title: \n", title)
  create_index('t', title, docID)


def findExternalLinks(external_links, docID):
  external_links_reg_exp = r'\[(.*?)\]'
  external_links = re.findall(external_links_reg_exp, external_links, flags=re.MULTILINE)
  external_links = ' '.join(external_links)
  # external_links = regex6.sub(' ',external_links)
  external_links = external_links.split()
  create_index("l", external_links, docID)
  # print("\n\nExternal links : \n", external_links)


def findInfoBox(content, docID):
  # print("\n\nInfobox: \n")
  for line in content:
    tokens = re.findall(r'=(.*?)\|',line,re.DOTALL)
    tokens = ' '.join(tokens)
    # tokens = regex6.sub(' ',tokens)
    tokens = tokens.split()
    create_index("i", tokens, docID)
    # print(tokens)


def process_content(content, docID):
  global current_index_file_no, inverted_index, indexed_tokens, limit


  content = content.lower()
  content = regex1.sub(' ', content)
  content = regex2.sub(' ', content)
  content = regex3.sub(' ', content)
  content = regex8.sub(' ', content)

  
  #infobox
  info_box_reg_exp = r'{{infobox(.*?)}}'
  infobox = re.findall(info_box_reg_exp, content, re.DOTALL)
  findInfoBox(infobox, docID)
  # print("\n\nInfobox: \n", findInfoBox(infobox))
  

  #categories
  category_reg_exp = r'\[\[category:(.*?)\]\]'
  categories = re.findall(category_reg_exp, content, flags=re.MULTILINE)
  categories = ' '.join(categories)
  # categories = regex6.sub(' ', categories)
  categories = categories.split()
  create_index("c", categories, docID)
  # print("\n\nCategories: \n", categories)

  #references
  references = []
  references_reg_exp = r'== ?references ?==(.*?)=='
  references = re.findall(references_reg_exp, content, flags=re.DOTALL)
  references = ' '.join(references)
  references = regex6.sub(' ', references)
  references = references.split()
  create_index("r", references, docID)
  # print("\n\nReferences: \n", references)

  #external links
  external_links_index = 0
  try:
    external_links_index = content.index('=external links=')+20
    try:
      category_index = content.index('[[category:')+20
      external_links = content[external_links_index : category_index]
      findExternalLinks(external_links, docID)
    except:
      pass
  except:
    pass

  #body
  body = content
  if external_links_index:
    body = content[0:external_links_index-20]

  ref_reg = re.compile(references_reg_exp,re.DOTALL)
  body = ref_reg.sub('',body)
  body = regex7.sub('',body)
  body = regex6.sub(' ',body)
  body = body.split()
  create_index("b", body, docID)
  # print("\n\nBody: \n", body)


  if docID%limit == 0:
    inverted_index_file_path = inverted_index_file_dir + "index_" + str(current_index_file_no) + ".txt"
    create_index_file(inverted_index_file_path)
    current_index_file_no = current_index_file_no + 1
    indexed_tokens += len(inverted_index)
    inverted_index = {}



def process_tags(elements):
  docID = elements.docID
  title = elements.title
  content = elements.text
  process_title(title, docID)
  process_content(content, docID)


class WikiHandler(xml.sax.ContentHandler):
  def __init__(self):
    self.current = ""
    self.docID = 0
    self.title = ""
    self.text = ""

  def startElement(self, name, attrs):
    self.current = name
    # print(name)

  def characters(self, content):
    if(self.current == "title"):
      self.title += content
    if self.current == "text":
      self.text += content
    # print()

  def endElement(self, name):
    if name == "page":
      self.docID += 1
      process_tags(self)
      doc_to_title.write(str(self.docID) + " " + self.title.strip() + "\n")
      self.title = ""
      self.text = ""
    # print()


if len(sys.argv) != 4:
	print("Invalid arguments")
	sys.exit(1)


wiki_dump_path = sys.argv[1]
inverted_index_file_dir = sys.argv[2]
inverted_index_stat_path = sys.argv[3]

dump_dir = wiki_dump_path + "*"

current_index_file_no = 1

doc_to_title_file = "DOC_ID_TO_TITLE.txt"
doc_to_title = open(doc_to_title_file, "w")
# word_to_doc_count = {}

try:
    os.mkdir(inverted_index_file_dir)
except FileExistsError:
    print("Directory already exists!")


stop_words = set()
# stop_words_file = "2019201003/stopwords.txt"
stop_words_file = "stopwords.txt"
try:
  f = open(stop_words_file,"r")
  for line in f:
    line = line.strip()
    stop_words.add(line)
except:
  print("Cannot find stopwords file")
  sys.exit(1)


limit = 30000
inverted_index = {}
total_number_of_tokens = 0
indexed_tokens = 0

start_time = timeit.default_timer()
wikihandler = WikiHandler()
parser = xml.sax.make_parser()
parser.setContentHandler(wikihandler)

# print(dump_dir)

dump_files = glob.glob(dump_dir)
for i in range(len(dump_files)):
  print(i," ",dump_files[i])
  parser.parse(dump_files[i])

if len(inverted_index) != 0:
  inverted_index_file_path = inverted_index_file_dir + "index_" + str(current_index_file_no) + ".txt"
  create_index_file(inverted_index_file_path)
  indexed_tokens += len(inverted_index)
  inverted_index = {}

print("Total number of index files : ", current_index_file_no)

create_index_stat_file(inverted_index_stat_path)

stop_time = timeit.default_timer()
print("Index creation time : ")
seconds = stop_time-start_time
minutes = float(seconds)/float(60)
hours = float(minutes)/float(60)
print(hours," hours")
print(minutes," minutes")
print(seconds," seconds")
