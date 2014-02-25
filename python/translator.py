#!/usr/bin/env python
import json
import math
import sys
import os
import re

from tag_reader import TagReader

class Translator:

	def __init__(self):
		self.dictionary = {}

	def tokenize(self, line):
		line = line.replace('.', '')
		line = line.replace(',', '')
		line = line.replace(';', '')
		line = line.replace(':', '')
		line = line.split()
		print line
		return line

	def read_dict(self, filename):
		"""Given the location of the dictionary, read it in and store it in the dictionary
		"""
		f = open(filename, 'r')
		for line in f:
			line = line.split(":")
			line[0] = unicode(line[0], encoding='utf-8')
			line[1] = line[1][:-1]
			self.dictionary[line[0]] = line[1]
	
	def read_tagged_corpus(self, filename):
		#Read in a corpus, as defined by the TagReader
		tr = TagReader()
		tr.read_data(filename)
		return tr.corpus
		
	def translation_to_str(self, translation):
		punctuation = ",.:;"
		str = ""
		for elem in translation:
			if elem[0] in punctuation:
				str = str + elem[0]
			else:
				str = str + " " + elem[0]
		return str
		
	def apply_postprocessing(self, translation):
		punctuation = ".,;:"
		#add articles
		i = 0
		while i < len(translation):
			word_duple = translation[i]
			word = word_duple[0]
			tag = word_duple[1]
			
			#Capitalize proper nouns:
			if tag[0] == 'N' and tag[1] == 'p':		#it's a proper noun
				new_word = word.capitalize()
				translation[i][0] = new_word
			i += 1
	
		#let's try to get Subject Verb Object word order
		print translation
	
	def translate(self, corpus_filename, tagged_corpus_filename):
		print "BEGINNING TRANSLATION\n"
		f = open(corpus_filename, 'r')
		punctuation = ".,;:"
		corpus = self.read_tagged_corpus(tagged_corpus_filename)
		for sentence in corpus:
			translation = []
			for word_triple in sentence:
				word = word_triple[0]
				tag_info = word_triple[1]	#not used yet
				lemma = word_triple[2]		#not used yet
				if word in punctuation:
					translation.append([word, word])
				elif word in self.dictionary:
					info = self.dictionary[word].split('.')
					english_word = info[0]		#info[1], if it exists, would be the Case (dat, gen, etc.),
												#  but the tagger should have provided this already
					english_word_duple = [english_word, tag_info]
					translation.append(english_word_duple)
			
			self.apply_postprocessing(translation)
			
			print "Original sentence:"
			print f.readline()[:-1]
			print "Translated as:"
			print self.translation_to_str(translation)
			print ""
		print "DONE"


def main(args):
	translator = Translator()
	translator.read_dict('../data/dictionary.txt')
	translator.translate('../data/two_sentences.txt', '../data/two_sentences_tagged.txt')

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)