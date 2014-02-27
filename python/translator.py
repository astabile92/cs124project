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
		self.punctuation = ".,;:"

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
		str = ""
		for elem in translation:
			if elem[0] in self.punctuation:
				str = str + elem[0]
			else:
				str = str + " " + elem[0]
		return str
		
	def apply_postprocessing(self, translation):
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
	
	#Needed for Strategy 2
	def flatten_list(self, list):
		result = []
		for elem in list:
			if not type(elem[0]) is str:
				for sub_elem in elem:
					result.append(sub_elem)
			else:
				result.append(elem)
		return result
	
	#STRATEGY 2
	"""
	Returns a NEW translation array
	"""
	def group_nouns_adj(self, old_translation):
		translation = old_translation[:]
		new_translation = []
		i = 0
		while i < len(translation):
			word_duple = translation[i]
			word = word_duple[0]
			tag = word_duple[1]
			if tag[0] == 'N':	#noun
				noun_case = tag[4]
				noun_phrase = []
				#Scan backwards:
				j = i - 1
				while j > 0 and not translation[j][0] in self.punctuation:
					other_tag = translation[j][1]
					if other_tag[0] == 'A' and other_tag[5] == noun_case:
						noun_phrase.append(translation[j])
						translation.pop(j)
						i -= 1
					j -= 1
				#Scan forwards:
				j = i + 1
				while j < len(translation) and not translation[j][0] in self.punctuation:
					other_tag = translation[j][1]
					if other_tag[0] == 'A' and other_tag[5] == noun_case:	#Adj with same Case as the noun
						noun_phrase.append(translation[j])
						translation.pop(j)
					else:
						j += 1
				noun_phrase.append(word_duple)
				new_translation.append(noun_phrase)
			else:
				has_noun = False
				j = i + 1
				while tag[0] == 'A' and j < len(translation) and not translation[j][0] in self.punctuation:
					other_tag = translation[j][1]
					if other_tag[0] == 'N' and other_tag[4] == tag[5]:
						has_noun = True
					j += 1
				if not has_noun:	#Make sure this is not an Adjective which is followed by a matching Noun
					new_translation.append(word_duple)
			i += 1
		return new_translation
	
	#STRATEGY 3
	"""
	Modifies the given translation array
	"""
	def interpret_genitives(self, translation):
		i = 0
		while i < len(translation):
			#do stuff
			word_duple = translation[i]
			word = word_duple[0]
			tag = word_duple[1]
			if tag[0] == 'N' and tag[4] == 'g':	#it's a genitive noun
				if i == 0 or not translation[i-1][1][0] == 'V' and not translation[i-1][1][0] == 'S':	#not preceded by a Verb OR "Adposition" (preposition)
					if i > 0 and translation[i-1][1][0] == 'M':		#preceded by numeral -- put "of" before that
						translation.insert(i-1, ["of", "#aux"])
					elif i > 0 and translation[i-1][1][0] == 'A' and translation[i-1][1][5] == 'g':	#preceded by genitive adjective
						translation.insert(i-1, ["of", "#aux"])
					else:
						translation.insert(i, ["of", "#aux"])					
					i += 1
			i += 1

	#STRATEGY 7
	def interpret_datives(self, translation):
		i = 0
		while i < len(translation):
			#do stuff
			word_duple = translation[i]
			word = word_duple[0]
			tag = word_duple[1]
			if (tag[0] == 'P' and tag[5] == 'd') or (tag[0] == 'N' and tag[4] == 'd'):	#it's a dative (pro)noun
				if i == 0 or not translation[i-1][1][0] == 'S':	#not preceded by an adposition already
					translation.insert(i, ["to", "#aux"])			#or also, "for"
					i += 1
			i += 1
	
	#STRATEGY 5
	#apply this AFTER moving around adjectives
	def add_articles(self, translation):
		i = 0
		vowels = "aeiou"
		while i < len(translation):
			#do stuff
			word_duple = translation[i]
			tag = word_duple[1]
			if tag[0] == 'N' and not tag[1] == 'p' and not tag[4] == 'g':		#non-proper noun, not in genitive case
				j = i - 1
				while j > 0 and translation[j][1][0] == 'A':
					j -= 1
				articles = ["the"]
				if tag[3] == 's':	#singular nouns could take 'a' or 'the'
					next_word = translation[j+1][0]
					if next_word[0] in vowels:
						articles.append("an")
					else:
						articles.append("a")
				translation.insert(j+1, [articles[-1], "#aux"])
				i += 1
			i += 1
	
	#STRATEGY 6
	def add_subjects(self, translation):
		i = 0
		found_noun = False
		while i < len(translation) and not translation[i][0] in self.punctuation:
			word_duple = translation[i]
			tag = word_duple[1]
			if tag[0] == 'N' or tag[0] == 'P':
				found_noun = True
			elif tag[0] == 'V' and not found_noun:
				if tag[5] == 's':
					translation.insert(i, ["it", "P--nsn--"])
				else:
					translation.insert(i, ["they", "P--npn--"])
				i += 1
			i += 1
	
	def translate(self, corpus_filename, tagged_corpus_filename):
		print "BEGINNING TRANSLATION\n"
		f = open(corpus_filename, 'r')		
		corpus = self.read_tagged_corpus(tagged_corpus_filename)
		for sentence in corpus:
			translation = []
			for word_triple in sentence:
				word = word_triple[0]
				tag_info = word_triple[1]	#not used yet
				lemma = word_triple[2]		#not used yet
				if word in self.punctuation:
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
			print "Initial translation:"
			print self.translation_to_str(translation)
			print "After genitive and dative handling:"
			self.interpret_genitives(translation)
			self.interpret_datives(translation)
			print self.translation_to_str(translation)
			print "After add articles and group adjectives:"
			new_translation = self.flatten_list(self.group_nouns_adj(translation))
			self.add_articles(new_translation)
			self.add_subjects(new_translation)
			print self.translation_to_str(new_translation)
			print new_translation
			print ""
		print "DONE"


def main(args):
	translator = Translator()
	translator.read_dict('../data/dictionary.txt')
	translator.translate('../data/dev_set.txt', '../data/dev_set_tagged.txt')

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)