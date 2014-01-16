# coding: utf-8

import sys
import feedparser
from xml.etree import ElementTree

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
	'link',
	'description'
]
item_optional = [
	'author',
	'category',
	'comments',
	('id', 'guid'),
	('published', 'pubDate')
] # enclosure, source

source = feedparser.parse(sys.argv[1])

root = ElementTree.Element('rss')
root.set('version', '2.0')

def put_elems(source, elems, xml_elem, required = False):
	for elem in elems:
		if isinstance(elem, tuple):
			attr = elem[0]
			tag = elem[1]
		else:
			attr = elem
			tag = elem

		if required or hasattr(source, attr):
			ElementTree.SubElement(xml_elem, tag).text = getattr(source, attr)

channel = ElementTree.SubElement(root, 'channel')
put_elems(source.feed, channel_required, channel, True)
put_elems(source.feed, channel_optional, channel)

for entry in source.entries:
	item = ElementTree.SubElement(channel, 'item')
	put_elems(entry, item_required, item, True)
	put_elems(entry, item_optional, item)

ElementTree.ElementTree(root).write(sys.argv[2], 'utf-8')

