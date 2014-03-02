#!/usr/bin/env python

import sys

class TagReader:

	def __init__(self):
		"""
		***How the Corpus works***
		self.corpus is a list of sentences, where each sentence is a list of "words":
		A "word" is a triple in the format: [russian word, tag info, russian word stem]
		For punctuation, I'll just fill the triple with that punctuation mark (e.g., [",", ",", ","])
		
		So, you might iterate through the corpus as follows:
		for sentence in self.corpus:
			for word_triple in sentence:
				#do stuff
		"""
		self.corpus = []	#see above

	"""
	This method just interprets the first character in the tag string (which indicates part of speech)
	This is the most basic information contained in the tag.
	For more detailed information about a given word (gender, case, etc.), see the 
	  following site for info on how to interpret the rest of the tag string:
	    http://corpus.leeds.ac.uk/mocky/msd-ru.html
	"""
	def part_of_speech(self, word):
		tag = word[1]
		category = tag[0]
		if category == 'N':
			return 'noun'
		elif category == 'V':
			return 'verb'
		elif category == 'A':
			return 'adjective'
		elif category == 'P':
			return 'pronoun'
		elif category == 'R':
			return 'adverb'
		elif category == 'S':
			return 'adposition'
		elif category == 'C':
			return 'conjunction'
		elif category == 'M':
			return 'numeral'
		elif category == 'Q':
			return 'particle'
		elif category == 'I':
			return 'interjection'
		elif category == 'Y':
			return 'abbreviation'
		elif category == 'X':
			return 'residual'
		return "punctuation"

	def word_to_str(self, word):
		return "%s\t%s\t%s" % (word[0], word[1], word[2]) 

	def read_data(self, filename):
		"""
		Read in the corpus at the given filename
		"""
		punctuation = '.,:;"-'
		cur_sentence = []
		f = open(filename, 'r')
		for line in f:
			line = unicode(line, encoding='utf-8')
			split_line = line.split()
			word = []
			if len(split_line) > 0 and split_line[0] in punctuation:
				punc = punctuation[punctuation.index(split_line[0])]
				word = [punc, punc, punc, ""]
			elif len(split_line) == 3:
				#Create the word-tuple: [russian word, tag info, russian lemma, slot for possible proposed english word]
				word = [split_line[0].lower(), split_line[1], split_line[2].lower(), ""]
			else:
				print "ERROR: TagReader couldn't process line: ", line
			
			cur_sentence.append(word)
			if len(word) > 0 and word[0] == '.':
				self.corpus.append(cur_sentence)
				cur_sentence = []

def main(args):
	tr = TagReader()
	tr.read_data('../data/two_sentences_tagged.txt')
	
	for sentence in tr.corpus:
		for word in sentence:
			print tr.word_to_str(word) + "\t(%s)" %tr.part_of_speech(word)

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)
