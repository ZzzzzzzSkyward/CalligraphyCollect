import re


class RevertIndex:
    def __init__(self):
        self.data = {}
        self.index = {}
        self.freq = {}

    def add_doc(self, id, doc):
        '''
        Args:
            id: any
            doc: text
        '''
        if id in self.data:
            print(id)
            print(doc)
            print(self.data[id])
            print('id already exists')
        self.data[id] = self.process_doc(id, doc)

    def process_doc(self, id, doc):
        '''
        parse the document and establish a list of tokens with their frequency
        then add them to the index
        return the list of tokens
        '''
        doc = doc.replace('\r', '').replace('\n', '').replace(
            '\t', '').replace('\ufeff', '').strip()
        tokens = self.parse_doc(doc)
        freq = {}
        for token in tokens:
            if token not in freq:
                freq[token] = 0
            freq[token] += 1
        for token in freq:
            if token not in self.index:
                self.index[token] = []
            self.index[token].append((id, freq[token]))
        return doc

    def sort_index(self):
        self.freq = {}
        for key in self.index:
            self.index[key].sort(key=lambda x: -x[1])
            self.freq[key] = 0
            for item in self.index[key]:
                self.freq[key] += item[1]
    chinese_unicode = [[0x4e00, 0x9fff], [0x3400, 0x4dff], [
        0x20000, 0x2a6df], [0xf900, 0xfaff], [0x2f800, 0x2faf1]]

    def is_chinese(self, word):
        u = ord(word)
        for i in self.chinese_unicode:
            if i[0] <= u <= i[1]:
                return True
        return False

    def is_string_chinese(self, string):
        for c in string:
            if not self.is_chinese(c):
                return False
        return True

    def parse_doc(self, doc):
        tokens = list(doc)
        chinese_tokens = [i for i in tokens if self.is_chinese(i)]
        return chinese_tokens

    def add_data(self, data):
        for id, doc in data.items():
            self.data[id] = doc

    def search(self, query):
        '''
        Args:
            query: text
        Returns:
            list of (id, data,count) pairs sorted by decreasing score
        '''
        # if it is a normal query
        normal = self.is_string_chinese(query)
        if normal:
            return self.search_normal(query)
        else:
            return self.search_regexp(query)

    def search_normal(self, query):
        print('normal')
        allhits = [self.index.get(c, None) for c in query]
        allhits = [[j[0] for j in i] for i in allhits if i]
        # get the intersect of list[list]
        hits = {j: True for i in allhits for j in i}
        hits = list(hits.keys())
        res = []
        if hits == None:
            pass
        else:
            for hit in hits:
                if hit in self.data and query in self.data[hit]:
                    res.append(
                        (hit, self.data[hit],  self.freq.get(query, 0)))
        return res

    def search_regexp(self, query):
        print('regexp')
        # if it is a regexp query
        regex = re.compile(query)
        res = []
        for id, doc in self.data.items():
            results = regex.findall(doc)
            count = len(results)
            if count > 0:
                res.append((id, doc, count))
        return res
