import argparse
import os.path
import requests
import sys
import time
import urllib.parse

from bs4 import BeautifulSoup, Tag, FeatureNotFound


def get_cmdline_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("search")
    parser.add_argument(
        "output", help="Path of the resulting RSS file. Use '-' for stdout"
    )
    parser.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        help="Specify that the output should be prettyfied",
    )

    return parser.parse_args()


def new_tag(tag: str, string: str) -> Tag:
    t = Tag(name=tag)
    t.string = string
    return t


def format_date(ts: time.struct_time) -> str:
    return time.strftime("%a, %d %b %Y %H:%M:%S +0000", ts)


def build(search: str, output: str, pretty: bool) -> None:
    rss = BeautifulSoup('<rss version="2.0" />').rss

    channel = Tag(name="channel")
    rss.append(channel)
    channel.append(new_tag("title", f"The Pirate Bay 🏴‍☠️ - {search}"))

    search = urllib.parse.quote(search)

    channel.append(new_tag("link", f"https://thepiratebay.org/search.php?q={search}"))
    channel.append(new_tag("description", "--"))
    channel.append(new_tag("lastBuildDate", format_date(time.gmtime())))
    channel.append(new_tag("generator", "RSS Builder"))

    r = requests.get(f"https://apibay.org/q.php?q={search}")

    for result in r.json():
        r = requests.get(f"https://apibay.org/t.php?id={result['id']}")
        details = r.json()

        description = f'<a href="magnet:?xt=urn:btih:{details["info_hash"]}">Magnet</a>'
        description += f"<pre>{details['descr']}</pre>"

        itemurl = f"https://thepiratebay.org/description.php?id={result['id']}"

        item = Tag(name="item")
        item.append(new_tag("title", result["name"]))
        item.append(new_tag("link", itemurl))
        item.append(new_tag("description", description))
        item.append(new_tag("pubDate", format_date(time.gmtime(details["added"]))))
        channel.append(item)

    out_func = lambda x: (x.prettify() if pretty else str(x))
    if output == "-":
        out_file = sys.stdout
        close_file = lambda: None
    else:
        dirname = os.path.dirname(output)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        out_file = open(output, "w")
        close_file = out_file.close

    out_file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
    out_file.write(out_func(rss))
    out_file.write("\n")
    close_file()


if __name__ == "__main__":
    args = get_cmdline_args()
    build(args.search, args.output, args.pretty)
