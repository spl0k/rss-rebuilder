# coding: utf-8

import time, re, argparse
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

def get_cmdline_arguments():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('url', help = 'URL of the source RSS file')
	argparser.add_argument('xpath', help = 'XPath expression used to extract the relevant content from the page linked by each RSS item')
	argparser.add_argument('output', help = 'Path of the resulting RSS file')
	return argparser.parse_args()

def rebuild_rss(url, xpath, output):
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
		linked_html = ElementTree.fromstring(fix_entities(r.content))

		try:
			content = ElementTree.tostring(linked_html.find(xpath))
		except AttributeError:
			content = 'XPath expression returned no result'
		except SyntaxError, e:
			content = 'Invalid XPath expression ({})'.format(e)

		ElementTree.SubElement(item, 'description').text = content

	ElementTree.ElementTree(root).write(output, 'utf-8')

if __name__ == '__main__':
	args = get_cmdline_arguments()
	rebuild_rss(args.url, args.xpath, args.output)

