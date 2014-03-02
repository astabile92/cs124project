#!/usr/bin/env python
import json
import math
import sys
import os
import re

from tag_reader import TagReader
from LaplaceBigramLanguageModel import LaplaceBigramLanguageModel

class Translator:

	def __init__(self):
		self.dictionary = {}
		self.punctuation = '.,;:"-'

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
		
	def capitalize(self, translation):
		#add articles
		first_word = True
		i = 0
		while i < len(translation):
			word_duple = translation[i]
			word = word_duple[0]			
			tag = word_duple[1]
			if first_word or (tag[0] == 'N' and tag[1] == 'p'):		#it's a proper noun or it starts the sentence
				new_word = word.capitalize()
				translation[i][0] = new_word
				if not word in self.punctuation:
					first_word = False
			i += 1
		
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
	def group_nouns_with_adj(self, old_translation):
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
		return self.flatten_list(new_translation)
	
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
		possible_results = []
		while i < len(translation):
			#do stuff
			word_duple = translation[i]
			word = word_duple[0]
			tag = word_duple[1]
			if (tag[0] == 'P' and tag[5] == 'd') or (tag[0] == 'N' and tag[4] == 'd'):	#it's a dative (pro)noun
				if i == 0 or not translation[i-1][1][0] == 'S':	#not preceded by an adposition already
					#Update possible results:
					for preposition in ["to", "for", "at"]:
						result = translation[:]
						result.insert(i, [preposition, "#aux"])
						possible_results.append(result)
					possible_results.append(translation[:])		#no preposition
					#Update passed-in translation:
					translation.insert(i, ["to", "#aux"])
					i += 1
			i += 1
		return possible_results
	
	#STRATEGY 5
	#apply this AFTER moving around adjectives
	def add_articles(self, translation):
		i = 0
		vowels = "aeiou"
		possible_results = []
		while i < len(translation):
			#do stuff
			word_duple = translation[i]
			tag = word_duple[1]
			if tag[0] == 'N' and not tag[1] == 'p':		#non-proper noun [, not in genitive case??]
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
				
				#Update possible results:
				for article in articles:
					result = translation[:]
					result.insert(j+1, [article, "#aux"])
					possible_results.append(result)
				possible_results.append(translation[:])		#no article
				#Update passed-in translation:
				translation.insert(j+1, [articles[-1], "#aux"])
				i += 1
			i += 1
		return possible_results
	
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
	
	#STRATEGY 8
	def shto_translate(self, russianSentence):
		for i in xrange(len(russianSentence)):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u0447\u0442\u043E':
				if i > 0 and russianSentence[i-1][0] == ',':
					russianSentence[i][3] = 'that'
				else:
					russianSentence[i][3] = 'what'

	#STRATEGY 10
	def kak_translate(self, russianSentence):
		for i in xrange(len(russianSentence)):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u043A\u0430\u043A':
				if i == len(russianSentence)-1 or 'V' in russianSentence[i+1][1]:
					russianSentence[i][3] = 'how'
				else:
					russianSentence[i][3] = 'like'

	#STRATEGY 4
	def he_has_she_has(self, russianSentence):
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

	#STRATEGY 9
	def negation(self, russianSentence):
		for i in xrange(len(russianSentence)):
			#unicode(russianSentence[i][0], encoding='utf-8').lower()
			if russianSentence[i][0] == u'\u043D\u0435':
				if russianSentence[i-1][0].startswith(u'\u043D\u0435') or russianSentence[i-1][0].startswith(u'\u043D\u0438'):
					russianSentence[i][3] = None
				else:
					#if i+1 < len(russianSentence) and 'V' in russianSentence[i+1][1]:
					#	russianSentence[i][3] = ['don\'t', 'didn\'t', 'did not', 'do not']
					#else:
					#	russianSentence[i][3] = 'not'
					russianSentence[i][3] = ['don\'t', 'didn\'t', 'did not', 'do not', 'not']
	
	def translate(self, corpus_filename, tagged_corpus_filename):
		print "BEGINNING TRANSLATION\n"
		f = open(corpus_filename, 'r')		
		corpus = self.read_tagged_corpus(tagged_corpus_filename)
		for sentence in corpus:
			direct_translation = []
			"""
			First, just do a direct translation for testing/analysis purposes
			"""
			for word_tuple in sentence:
				word = word_tuple[0]
				tag_info = word_tuple[1]
				if word in self.punctuation or word not in self.dictionary:
					direct_translation.append([word, word])
				else:	#it's a russian word, look it up in the dictionary
					info = self.dictionary[word].split('.')
					english_word = info[0]		#info[1], if it exists, would be the Case (dat, gen, etc.),
												#  but the tagger will provide this instead
					english_word_duple = [english_word, tag_info]
					direct_translation.append(english_word_duple)
			
			"""
			Now we have a direct translation.
			Time for da real shiz
			Apply russian -> russian rules
			"""
			self.shto_translate(sentence)
			self.kak_translate(sentence)
			self.he_has_she_has(sentence)
			self.negation(sentence)
			"""
			Now, do the "direct" translation
			"""
			translation_candidates = []
			translation_candidates.append([])
			for word_tuple in sentence:
				word = word_tuple[0]
				tag_info = word_tuple[1]
				english_candidate = word_tuple[3]
				for tc in translation_candidates[:]:
					if word in self.punctuation:
						tc.append([word, word])
					elif not english_candidate == None:
						if type(english_candidate) is str:
							if english_candidate == "":
								"""
								There was no proposed candidate, so translate from the dictionary
								"""
								info = self.dictionary[word].split('.')
								english_word = info[0]		#info[1], if it exists, would be the Case (dat, gen, etc.),
													#  but the tagger should have provided this already
								english_word_duple = [english_word, tag_info]
								tc.append(english_word_duple)
							else:
								tc.append([english_candidate, tag_info])
						else:
							"""
							There was a list of possible english words, so generate multiple candidates
							"""
							tc.append([english_candidate[0], tag_info])
							for i in xrange( 1, len(english_candidate)):
								translation = tc[:-1]
								translation.append([english_candidate[i], tag_info])
								translation_candidates.append(translation)	
			"""
			At this point, the russian -> russian rules have been applied
			Now, apply the english -> english rules, and continue keeping track of candidates
			"""
			#translation_candidates = [ translation[:] ]
			#Apply Genitive rule:
			for tc in translation_candidates:
				self.interpret_genitives(tc)
			#Apply Dative rule (many possible results):
			all_results = []
			for tc in translation_candidates:
				results = self.interpret_datives(tc[:])
				for r in results:
					all_results.append(r)
			for r in all_results:
				translation_candidates.append(r)
			#Apply reordering rule:
			old_candidates = translation_candidates[:]
			for t in old_candidates:
				new_t = self.group_nouns_with_adj(t)
				translation_candidates.append(new_t)
			#Apply articles rule:
			all_results = []
			for tc in translation_candidates:
				results = self.add_articles(tc[:])
				for r in results:
					all_results.append(r)
			for r in all_results:
				translation_candidates.append(r)
			#Apply subjects rule:
			for tc in translation_candidates:
				self.add_subjects(tc)
				
			"""
			Now do some purely aesthetic formatting (capitalization)
			Note this won't mess up the language model
			"""		
			self.capitalize(direct_translation)
			for tc in translation_candidates:
				self.capitalize(tc)
			"""
			Now, build the Language Model, which will choose the best candidate
			"""
			#DRAFT
			train_file = open('../data/language_model_training_corpus.txt')
			trainingCorpus = []
			for line in train_file:
			    sentence = re.findall(r"[\w']+|[.,!?;]", line.lower())
			    if len(sentence) > 0:
			        sentence = ['<s>'] + sentence + ['</s>']
			        trainingCorpus.append(sentence)
			lm = LaplaceBigramLanguageModel(trainingCorpus)
			"""
			Finally, use the Language Model to pick the best candidate!
			"""
			maxScore = float("-inf")
			maxScoreSentence = ""
			for tc in translation_candidates:
				tc_string = self.translation_to_str(tc)
				sentence = re.findall(r"[\w']+|[.,!?;]", tc_string.lower())
				if len(sentence) > 0:
					sentence = ['<s>'] + sentence + ['</s>']
					score = lm.score(sentence)
					#print tc_string
					#print "\tScore: ", score
					if score > maxScore:	#normalizing here!
						maxScore = score
						maxScoreSentence = tc_string
			"""
			Output the results!!
			"""
			print "Original sentence:"
			print f.readline()[:-1]
			print "Direct translation:"
			print self.translation_to_str(direct_translation)
			"""
			print "All translation candidates:"
			for tc in translation_candidates:
				print self.translation_to_str(tc)
			"""
			print "Best translation as chosen by LM:"
			print maxScoreSentence
			print ""
		print "DONE"

def main(args):
	translator = Translator()
	translator.read_dict('../data/dictionary.txt')
	"""
	The translator reads the original russian sentences (dev_set.txt) but also
	needs a file tagged with Part-Of-Speech information (dev_set_tagged.txt)
	"""
	translator.translate('../data/dev_set.txt', '../data/dev_set_tagged.txt')

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)