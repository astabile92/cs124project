#!/usr/bin/env python
import json
import math
import sys
import os
import re

class Translator:

	def __init__(self):
		self.dictionary = {}
		self.foreignText = []

	def tokenize(self, line):
		line = line.replace('.', '')
		line = line.replace(',', '')
		line = line.replace(';', '')
		line = line.replace(':', '')
		line = line.split()
		print line
		return line

	def read_data(self, filename):
		"""
		Given the location of the story, read it in one line at a time
		"""
		print "Reading in documents ..."
		f = open(filename, 'r')
		for line in f:
			line = unicode(line, encoding='utf-8').lower()
			line = self.tokenize(line)
			print line
			self.foreignText.append(line)
			#print self.foreignText

	def read_dict(self, filename):
		"""Given the location of the dictionary, read it in and store it in the dictionary
		"""
		f = open(filename, 'r')
		for line in f:
			line = line.split(":")
			line[0] = unicode(line[0], encoding='utf-8')
			line[1] = line[1][:-1]
			self.dictionary[line[0]] = line[1]
		#print self.dictionary

	def translate(self):
		sentence = []
		for line in self.foreignText:
			sentence = []
			for word in line:
				if word in self.dictionary:
					sentence.append(self.dictionary[word])
			print sentence
			print '\n'


def main(args):
	translator = Translator()
	translator.read_data('../data/Lady_With_Toy_Dog.txt')
	translator.read_dict('../data/dictionary.txt')
	translator.translate()

if __name__ == '__main__':
	args = sys.argv[1:]
	main(args)