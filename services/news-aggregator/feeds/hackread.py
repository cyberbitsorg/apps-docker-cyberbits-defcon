from feeds.base import RssFeedParser


class HackReadFeed(RssFeedParser):
    source_id = "hackread"
    feed_url = "https://hackread.com/feed/"
