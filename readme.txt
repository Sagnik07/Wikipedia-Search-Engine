Index splits :
 
Index file is split into 100 smaller files while merging. The split is made in a manner such that every index file contains not more than 75000
words (tokens). These files are numbered as "index1.txt" to "index100.txt"
A secondary index file is also maintained to store the first word of each index file and it's corresponding file number.
The secondary index file is named as "secondary_index.txt"


A word-to-position mapping is maintained in a file named "WORD_TO_POSITION.json".
This file contains each word and it's corresponding position in it's index file.

Search :

During search time, first the secondary index file is searched to find the file (primary index file) where the word is present.
Then we open the primary index file of the word and search for it's postings list using the fseek command.
The offset is obtained from the file "WORD_TO_POSITION.json".

This way, searching the file everytime for a word is optimized.
