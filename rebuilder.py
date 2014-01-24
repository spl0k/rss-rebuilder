# coding: utf-8

import time, re, argparse
import feedparser, requests
from htmlentitydefs import name2codepoint
from bs4 import BeautifulSoup, Tag
try:
	from bs4 import FeatureNotFound
except ImportError:
	FeatureNotFound = ValueError

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
			e = Tag(name = tag)
			e.string = getattr(source, attr)
			xml_elem.append(e)

def get_cmdline_arguments():
	argparser = argparse.ArgumentParser()
	argparser.add_argument('url', help = 'URL of the source RSS file')
	argparser.add_argument('selector', help = 'CSS selector used to extract the relevant content from the page linked by each RSS item')
	argparser.add_argument('output', help = 'Path of the resulting RSS file')
	return argparser.parse_args()

def rebuild_rss(url, selector, output):
	source = feedparser.parse(url)

	try:
		soup = BeautifulSoup('<rss version="2.0" />', 'xml')
		rss = soup.rss
		has_lxml = True
	except FeatureNotFound:
		rss = BeautifulSoup('<rss version="2.0" />').rss
		has_lxml = False

	channel = Tag(name = 'channel')
	rss.append(channel)
	putback_elems(source.feed, channel_required, channel, True)
	putback_elems(source.feed, channel_optional, channel)

	build_date = Tag(name = 'lastBuildDate')
	build_date.string = time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())
	channel.append(build_date)

	generator = Tag(name = 'generator')
	generator.string = source.feed.generator + ' & RSS Rebuilder' if hasattr(source.feed, 'generator') else 'RSS Rebuilder'
	channel.append(generator)

	for entry in source.entries:
		item = Tag(name = 'item')
		channel.append(item)

		putback_elems(entry, item_required, item, True)
		putback_elems(entry, item_optional, item)

		r = requests.get(entry.link)
		linked_html = BeautifulSoup(r.content, 'lxml') if has_lxml else BeautifulSoup(r.content)
		content = reduce(lambda s, tag: s + repr(tag), linked_html.select(selector), '')

		desc = Tag(name = 'description')
		desc.string = content
		item.append(desc)

	with open(output, 'w') as out_file:
		if has_lxml:
			out_file.write(str(soup))
		else:
			out_file.write('<?xml version="1.0" encoding="UTF-8" ?>')
			out_file.write(str(rss))

if __name__ == '__main__':
	args = get_cmdline_arguments()
	rebuild_rss(args.url, args.selector, args.output)

