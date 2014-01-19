# coding: utf-8

import sys, time, re
import feedparser, requests
from xml.etree import ElementTree
from htmlentitydefs import name2codepoint

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

def fix_entities(text):
	text = re.sub('&([a-z][a-z0-9]+);', lambda match: '&#{};'.format(name2codepoint[match.group(1)]), text)
	text = re.sub('&([_a-z0-9]+)([^;])', lambda match: '&amp;{}{}'.format(match.group(1), match.group(2)), text)
	text = text.replace(' & ', ' &amp; ')
	return text

source = feedparser.parse(sys.argv[1])

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
	linked_html = ElementTree.fromstring(fix_entities(r.content))

	try:
		content = ElementTree.tostring(linked_html.find(sys.argv[2]))
	except AttributeError:
		content = 'XPath expression returned no result'
	except SyntaxError, e:
		content = 'Invalid XPath expression ({})'.format(e)

	ElementTree.SubElement(item, 'description').text = content

ElementTree.ElementTree(root).write(sys.argv[3], 'utf-8')

