from feeds.base import RssFeedParser


class CybernewsFeed(RssFeedParser):
    source_id = "cybernews"
    feed_url = "https://cybernews.com/feed/"
