#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
		self.sentenceWithInformation = []

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
		#perhaps also for adding articles?
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
				"""
				if not tag[1] == 'p':	#it's not a proper noun
					noun_phrase.insert(0, ["the", "#aux"])
				"""
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
					print "BOOM - Genitive Noun: ", word
					if i > 0 and translation[i-1][1][0] == 'M':		#preceded by numeral -- put "of" before that
						translation.insert(i-1, ["of", "#aux"])
					elif i > 0 and translation[i-1][1][0] == 'A' and translation[i-1][1][5] == 'g':	#preceded by genitive adjective
						translation.insert(i-1, ["of", "#aux"])
					else:
						translation.insert(i, ["of", "#aux"])					
					i += 1
			i += 1

	def translate(self, corpus_filename, tagged_corpus_filename):
		print "BEGINNING TRANSLATION\n"
		f = open(corpus_filename, 'r')		
		corpus = self.read_tagged_corpus(tagged_corpus_filename)
		for sentence in corpus:
			translation = []
			sentenceList = []
			for word_triple in sentence:
				word = word_triple[0]
				tag_info = word_triple[1]	#not used yet
				lemma = word_triple[2]		#not used yet
				sentenceList.append([word, tag_info, lemma, ''])
				if word in self.punctuation:
					translation.append([word, word])
				elif word in self.dictionary:
					info = self.dictionary[word].split('.')
					english_word = info[0]		#info[1], if it exists, would be the Case (dat, gen, etc.),
												#  but the tagger should have provided this already
					english_word_duple = [english_word, tag_info]
					translation.append(english_word_duple)
			self.sentenceWithInformation.append(sentenceList)
			self.apply_postprocessing(translation)
						
			# print "Original sentence:"
			# print f.readline()[:-1]
			print sentenceList
			self.shto_translate(sentenceList)
			print sentenceList
			self.kak_translate(sentenceList)
			print sentenceList
			self.he_has_she_has(sentenceList)
			print sentenceList
			self.negation(sentenceList)
			print sentenceList
			print "\n\n\n"
			# print "Initial translation:"
			# print self.translation_to_str(translation)
			# print "After genitive handling:"
			# self.interpret_genitives(translation)
			# print self.translation_to_str(translation)
			# print "After group adjectives:"
			# new_translation = self.group_nouns_adj(translation)
			# print self.translation_to_str(self.flatten_list(new_translation))
			# print new_translation
			print ""
		print "DONE"
#============divya===========================================
	def shto_translate(self, russianSentence):
		print "SHTOOOOOO"
		for i in xrange(len(russianSentence)):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u0447\u0442\u043E':
				if i > 0 and russianSentence[i-1][0] == ',':
					russianSentence[i][3] = 'that'
				else:
					russianSentence[i][3] = 'what'
				print russianSentence
		print "done with shtoooo"

	def kak_translate(self, russianSentence):
		print "KAK"
		for i in xrange(len(russianSentence)):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u043A\u0430\u043A':
				if i == len(russianSentence)-1 or 'V' in russianSentence[i+1][1]:
					russianSentence[i][3] = 'how'
				else:
					russianSentence[i][3] = 'like'
				print russianSentence
		print "done with kak"

	def he_has_she_has(self, russianSentence):
		print "he/she has"
		wasWords = [u'\u0431\u044B\u043B\u0430', u'\u0431\u044B\u043B', u'\u0431\u044B\u043B\u043E']
		for i in xrange(len(russianSentence)-1):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u0443' or russianSentence[i][0] == u'\u0423':
				if russianSentence[i+1][0] == u'\u043D\u0435\u0433\u043E':#HE has
					russianSentence[i][3] = 'he'
					if i+2 < len(russianSentence)-1 and russianSentence[i+2][0] in wasWords:#he HAD
						russianSentence[i+1][3] = 'had'
						russianSentence[i+2][3] = None#SHOULD I JUST REMOVE THE 'WAS' WORD FROM THE SENTENCE ENTIRELY OR LEAVE IT AS A BLANK? WILL LEAVING THE RUSSIAN WORD IN CAUSE PROBLEMS LATER?
					else:#he HAS
						russianSentence[i+1][3] = 'has'
						
				if russianSentence[i+1][0] == u'\u043D\u0435\u0435':#SHE has
					russianSentence[i][3] = 'she'
					if i+2 < len(russianSentence)-1 and russianSentence[i+2][0] in wasWords:#she HAD
						russianSentence[i+1][3] = 'had'
						russianSentence[i+2][3] = None#SHOULD I JUST REMOVE THE 'WAS' WORD FROM THE SENTENCE ENTIRELY OR LEAVE IT AS A BLANK? WILL LEAVING THE RUSSIAN WORD IN CAUSE PROBLEMS LATER?
					else:#she HAS
						russianSentence[i+1][3] = 'has'
				print russianSentence
		print "done with he has/she has"

	def negation(self, russianSentence):
		print "negation!"
		for i in xrange(len(russianSentence)):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u043D\u0435':#не
				if russianSentence[i-1][0].startswith(u'\u043D\u0435'):
					russianSentence[i][3] == None
				else:
					if i+1 < len(russianSentence) and 'V' in russianSentence[i+1][1]:
						russianSentence[i][3] = ['don\'t', 'didn\'t', 'did not', 'do not']
					else:
						russianSentence[i][3] = 'not'
				print russianSentence
		print "done with negation"




def main(args):
	translator = Translator()
	translator.read_dict('../data/dictionary.txt')
	translator.translate('../data/dev_set.txt', '../data/dev_set_tagged.txt')

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)