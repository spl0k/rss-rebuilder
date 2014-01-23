# coding: utf-8

import time, re, argparse
import feedparser, requests
from xml.etree import ElementTree
from htmlentitydefs import name2codepoint
from bs4 import BeautifulSoup

channel_required = [
	'title',
	'link',
	'description'
]
channel_optional = [
	'language',
	('rights', 'copyright'),
	('author', 'managingEditor'),
	('publisher', 'webMaster'),
	('published', 'pubDate'),
	'category',
	'docs',
	'ttl',
	'rating',
	'skipHours',
	'skipDays'
] # lastBuildDate, generator, cloud, image, textInput
item_required = [
	'title',
	'link'
] # description
item_optional = [
	'author',
	'category',
	'comments',
	('id', 'guid'),
	('published', 'pubDate')
] # enclosure, source

def putback_elems(source, elems, xml_elem, required = False):
	for elem in elems:
		if isinstance(elem, tuple):
			attr = elem[0]
			tag = elem[1]
		else:
			attr = elem
			tag = elem

		if required or hasattr(source, attr):
			ElementTree.SubElement(xml_elem, tag).text = getattr(source, attr)

def get_cmdline_arguments():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('url', help = 'URL of the source RSS file')
	argparser.add_argument('selector', help = 'CSS selector used to extract the relevant content from the page linked by each RSS item')
	argparser.add_argument('output', help = 'Path of the resulting RSS file')
	return argparser.parse_args()

def rebuild_rss(url, selector, output):
	source = feedparser.parse(url)

	root = ElementTree.Element('rss')
	root.set('version', '2.0')

	channel = ElementTree.SubElement(root, 'channel')
	putback_elems(source.feed, channel_required, channel, True)
	putback_elems(source.feed, channel_optional, channel)

	ElementTree.SubElement(channel, 'lastBuildDate').text = time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())
	if hasattr(source.feed, 'generator'):
		ElementTree.SubElement(channel, 'generator').text = source.feed.generator + ' & RSS Rebuilder'
	else:
		ElementTree.SubElement(channel, 'generator').text = 'RSS Rebuilder'

	for entry in source.entries:
		item = ElementTree.SubElement(channel, 'item')
		putback_elems(entry, item_required, item, True)
		putback_elems(entry, item_optional, item)

		r = requests.get(entry.link)
		linked_html = BeautifulSoup(r.content)
		content = reduce(lambda s, tag: s + repr(tag), linked_html.select(selector), '')

		ElementTree.SubElement(item, 'description').text = content

	with open(output, 'w') as out_file:
		out_file.write('<?xml version="1.0" encoding="UTF-8" ?>')
		ElementTree.ElementTree(root).write(out_file, 'utf-8')

if __name__ == '__main__':
	args = get_cmdline_arguments()
	rebuild_rss(args.url, args.selector, args.output)

