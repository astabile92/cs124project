import math, collections, re, sys

class LaplaceBigramLanguageModel:

  def __init__(self, corpus):
    self.LaplaceUnigramCounts = collections.defaultdict(lambda: 0)
    self.LaplaceBigramCounts = collections.defaultdict(lambda: 0)
    self.total = 0
    self.V = 0
    self.train(corpus)

  def train(self, corpus):
    for sentence in corpus:
        previousWord = ''
        for token in sentence:
            self.LaplaceUnigramCounts[token] = self.LaplaceUnigramCounts[token] + 1
            if previousWord == '':
                previousWord = token
            else:
                bigram = previousWord+token
                previousWord = token
                self.LaplaceBigramCounts[bigram] = self.LaplaceBigramCounts[bigram] + 1

            self.total += 1
    self.V = len(self.LaplaceUnigramCounts)
    self.total = sum(self.LaplaceUnigramCounts.values())

  #note that this isn't normalizing at all by the length of the sentence...should it?
  def score(self, sentence):
    score = 0.0
    for i in xrange(1,len(sentence)):
        bigram = sentence[i-1]+sentence[i]
        count = self.LaplaceBigramCounts[bigram]
        score += math.log(count+1)
        unigramCount = self.LaplaceUnigramCounts[sentence[i-1]]
        score -= math.log(unigramCount+self.V)
    score /= len(sentence)
    return score



def main(args):
    trainPath = '../data/language_model_training_corpus.txt'
    f = open(trainPath)
    trainingCorpus = []
    for line in f:
        sentence = re.findall(r"[\w']+|[.,!?;]", line.lower())
        if len(sentence) > 0:
            sentence = ['<s>'] + sentence + ['</s>']
            trainingCorpus.append(sentence)
    
    lm = LaplaceBigramLanguageModel(trainingCorpus)
    testPath = '../data/translator_output.txt'
    f2 = open(testPath)
    maxScore = float("-inf")
    maxScoreSentence = ''
    for line in f2:
        sentence = re.findall(r"[\w']+|[.,!?;]", line.lower())
        if len(sentence) > 0:
            sentence = ['<s>'] + sentence + ['</s>']
            score = lm.score(sentence)
            print sentence
            print score
            if score > maxScore:
                maxScore = score
                maxScoreSentence = line
    print "\n\nBEST:"
    print maxScoreSentence
    print maxScore

if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)


