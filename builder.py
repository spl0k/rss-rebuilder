# coding: utf-8

import time, argparse, sys

def get_cmdline_args():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('url', help = 'URL to get the list of articles from')
    argparser.add_argument('list_selector', help = 'CSS selector to retreive items URLs (<a> tags)')
    argparser.add_argument('item_selector', help = 'CSS selector used to extract the relevant content from the URL the previous selector returned.')
    argparser.add_argument('output', help = 'Path of the resulting RSS file. Use "-" for stdout')
    argparser.add_argument('-p', '--pretty', action = 'store_true', help = 'Specify that the output should be prettyfied')
    argparser.add_argument('--ignored-query-params', nargs = '*', default = [], help = 'Query parameters to remove when generating the links')
    return argparser.parse_args()

def new_tag(tag, string):
    t = Tag(name = tag)
    t.string = string
    return t

def build_rss(url, list_selector, item_selector, ignored_qp, output, pretty = False):
    try:
        soup = BeautifulSoup('<rss version="2.0" />', 'xml')
        rss = soup.rss
        has_lxml = True
    except FeatureNotFound:
        rss = BeautifulSoup('<rss version="2.0" />').rss
        has_lxml = False

    r = requests.get(url)
    list_html = (BeautifulSoup(r.text, 'lxml') if has_lxml else BeautifulSoup(r.text)).html

    channel = Tag(name = 'channel')
    rss.append(channel)
    channel.append(new_tag('title', list_html.head.title.string))
    channel.append(new_tag('link', url))
    channel.append(new_tag('description', '--'))
    channel.append(new_tag('lastBuildDate', time.strftime('%a, %d %b %Y %H:%M:%S +0000', time.gmtime())))
    channel.append(new_tag('generator', 'RSS Builder'))

    item_urls = list_html.select(list_selector)
    for item_url in map(lambda i: i['href'], item_urls):
        item_url = urlparse.urljoin(url, item_url)
        parsed = urlparse.urlparse(item_url)
        query_params = urlparse.parse_qsl(parsed.query)
        item_url = urlparse.urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            '&'.join([ k+'='+v for k, v in query_params if k not in ignored_qp ]),
            parsed.fragment))

        r = requests.get(item_url)
        item_html = (BeautifulSoup(r.text, 'lxml') if has_lxml else BeautifulSoup(r.text)).html

        item = Tag(name = 'item')
        item.append(new_tag('title', item_html.head.title.string))
        item.append(new_tag('link', item_url))
        item.append(new_tag('description', str(item_html.select(item_selector)[0])))
        channel.append(item)

    out_func = lambda x: (x.prettify() if pretty else unicode(x)).encode('utf-8')
    if output == '-':
        out_file = sys.stdout
        close_file = lambda: None
    else:
        out_file = open(output, 'w')
        close_file = out_file.close

    if has_lxml:
        out_file.write(out_func(soup))
    else:
        out_file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        out_file.write(out_func(rss))
    out_file.write('\n')
    close_file()

if __name__ == '__main__':
    args = get_cmdline_args()

    import feedparser, requests, urlparse
    from bs4 import BeautifulSoup, Tag
    try:
        from bs4 import FeatureNotFound
    except ImportError:
        FeatureNotFound = ValueError

    build_rss(args.url, args.list_selector, args.item_selector, args.ignored_query_params, args.output, args.pretty)

