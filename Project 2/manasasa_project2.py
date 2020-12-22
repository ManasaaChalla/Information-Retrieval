import sys
import operator
import re
import json
import nltk  # needed for
nltk.download('punkt') #getting libraries
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

outfile=sys.argv[2]
queriesFile=sys.argv[3]
IndexFile=sys.argv[1]

ps = PorterStemmer()
stopwords = set(stopwords.words('english'))


def word_tokenize(line):
    return re.split(r'[\s-]+', line)


def ExtractLine(line):
    data = line.split('\t')
    if len(data) < 1:
        return None
    return data[0], data[1]


def CleanLine(line):
    return re.sub(r'[^a-z\s0-9-]', ' ', line.strip().lower())


def StemWords(words):
    stemmed = []
    for word in words:
        stem = ps.stem(word)
        if stem in stemmed:
            continue
        stemmed.append(stem)
    return stemmed


def RemoveStopWords(words):
    return [x for x in words if x not in stopwords]


def ReadInput(filename):
    file1 = open(filename,encoding="utf-8")
    Lines = file1.readlines()
    file1.close()
    return Lines


def main():
    linked_list = ProcessLibrary()
    #print(linked_list.traverse_list())
    #print(GetIndexesOfstemmedWord("etiopathogenesi", linked_list))
    SearchWords = ProcessSearch()
    Searches = ConvertSearchesIntoIndex(SearchWords, linked_list)
    with open(outfile, 'w') as outfilePointer:
        json.dump(Searches, outfilePointer)
    #print(json.dumps(Searches))


def ProcessSingleSearch(SearchWordList, linked_list):
    MaxDocId = -1
    MinDocId = -1
    Indexes = []
    for word in SearchWordList:
        Stimpack = GetIndexesOfstemmedWord(word, linked_list)
        Indexes.append([word, Stimpack])
        if MinDocId == -1:
            MinDocId = Stimpack[0]
        elif MinDocId > Stimpack[0]:
            MinDocId = Stimpack[0]
        if MaxDocId == -1:
            MaxDocId = Stimpack[-1]
        elif Stimpack[-1] < MaxDocId:
            MaxDocId = Stimpack[-1]
    for IndexList in Indexes:
        IndexList[1] = set(filter(lambda e: e >= MinDocId and e <= MaxDocId, IndexList[1]))
    return Indexes


def ConvertSearchesIntoIndex(SearchWords, linked_list):
    jsonData = dict()
    jsonData["postingsList"] = dict()
    jsonData["daatAnd"] = dict()
    for SearchWordListItems in SearchWords:
        SearchWordList = SearchWordListItems[0]
        Indexes = ProcessSingleSearch(SearchWordList, linked_list)
        for Index in Indexes:
            res = list(Index[1])
            res.sort()
            jsonData["postingsList"][Index[0]] = res

        JustIndexes = map(lambda x: x[1], Indexes)
        Compares = 0
        for i in Indexes:
            Compares += len(i[1])
        InterSects = list(set.intersection(*JustIndexes))
        InterSects.sort()
        SearchPhrase = SearchWordListItems[1]
        jsonData["daatAnd"][SearchPhrase] = dict()
        jsonData["daatAnd"][SearchPhrase]["results"] = InterSects
        jsonData["daatAnd"][SearchPhrase]["num_docs"] = len(InterSects)
        jsonData["daatAnd"][SearchPhrase]["num_comparisons"] = Compares
    return jsonData

def ProcessSearch():
    Lines = ReadInput(queriesFile)
    Data = []
    for line in Lines:
        #print("Input query -> ",line)
        WordString = CleanLine(line)
        #print("Query Post Processing -> ",WordString)
        cleaned_line = CleanLine(WordString)
        tokens = word_tokenize(cleaned_line)
        #print("Doc tokens post whitespace tokenizing -> ",tokens)
        t = RemoveStopWords(tokens)
        #print("Doc tokens post stopword removal -> ",t)
        stemmed = StemWords(t)
        #print("Doc tokens post stemming -> ",stemmed,"\n")
        Data.append([stemmed, line.strip()])
    return Data


def ProcessLibrary():
    linked_list = LinkedList()
    Lines = ReadInput(IndexFile)
    Data = []
    maps = dict()
    for line in Lines:
        #print("Input -> ",line)
        docId, WordString = ExtractLine(line)
        #print ("Doc id -> "+docId)
        #print("Doc text -> "+WordString+"\n")
        if docId is None:
            continue
        cleaned_line = CleanLine(WordString)
        #print("Doc text post processing -> ",cleaned_line,"\n") 
        tokens = word_tokenize(cleaned_line)
        #print("Doc tokens post whitespace tokenizing -> ",tokens)
        t = RemoveStopWords(tokens)
        #print("Doc tokens post stopword removal -> ",t)
        stemmed = StemWords(t)
        #print("Doc tokens post stemming -> ",stemmed,"\n")
        Data.append([int(docId), stemmed])
    sorted_list = sorted(Data, key=operator.itemgetter(0))
    for doc in sorted_list:
        DocID = doc[0]
        Words = doc[1]
        for word in Words:
            if word not in maps.keys():
                maps[word] = []
            if DocID not in maps[word]:
                maps[word].append(DocID)
    for word in maps.keys():
        linked_list.insert_at_end([word, maps[word]])
    return linked_list


def GetIndexesOfstemmedWord(word, linkedList):
    start = linkedList.start_node
    while start is not None:
        if start.value[0] == word:
            return start.value[1]
        start = start.next
    return None

class Node:
    def __init__(self, value = None, next = None):
        self.value = value
        self.next = next

class LinkedList:

    def __init__(self, index=0, mode="simple"):
        self.start_node = None # Head pointer
        self.end_node = None # Tail pointer
        # Additional attributes
        self.index = index
        self.mode = "simple"

    # Method to traverse a created linked list
    def traverse_list(self):
        traversal = []
        if self.start_node is None:
            print("List has no element")
            return
        else:
            n = self.start_node
            # Start traversal from head, and go on till you reach None
            while n is not None:
                traversal.append(n.value)
                n = n.next
            return traversal

    # Method to insert elements in the linked list
    def insert_at_end(self, value):
        # determine data type of the value
        if 'list' in str(type(value)):
            self.mode = "list"

        # Initialze a linked list element of type "Node"
        new_node = Node(value)
        n = self.start_node # Head pointer

        # If linked list is empty, insert element at head
        if self.start_node is None:
            self.start_node = new_node
            self.end_node = new_node
            return "Inserted"

        elif self.mode == "list":
            if self.start_node.value[self.index] >= value[self.index]:
                self.start_node = new_node
                self.start_node.next = n
                return "Inserted"

            elif self.end_node.value[self.index] <= value[self.index]:
                self.end_node.next = new_node
                self.end_node = new_node
                return "Inserted"

            else:
                while value[self.index] > n.value[self.index] and value[self.index] < self.end_node.value[self.index] and n.next is not None:
                    n = n.next

                m = self.start_node
                while m.next != n and m.next is not None:
                    m = m.next
                m.next = new_node
                new_node.next = n
                return "Inserted"
        else:
            # If element to be inserted has lower value than head, insert new element at head
            if self.start_node.value >= value:
                self.start_node = new_node
                self.start_node.next = n
                return "Inserted"

            # If element to be inserted has higher value than tail, insert new element at tail
            elif self.end_node.value <= value:
                self.end_node.next = new_node
                self.end_node = new_node
                return "Inserted"

            # If element to be inserted lies between head & tail, find the appropriate position to insert it
            else:
                while value > n.value and value < self.end_node.value and n.next is not None:
                    n = n.next

                m = self.start_node
                while m.next != n and m.next is not None:
                    m = m.next
                m.next = new_node
                new_node.next = n
                return "Inserted"

if __name__ == '__main__':
    main()
