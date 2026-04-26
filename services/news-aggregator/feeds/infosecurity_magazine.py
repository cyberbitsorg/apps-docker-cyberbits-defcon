from feeds.base import RssFeedParser


class InfosecurityMagazineFeed(RssFeedParser):
    source_id = "infosecurity_magazine"
    feed_url = "https://www.infosecurity-magazine.com/rss/news/"
