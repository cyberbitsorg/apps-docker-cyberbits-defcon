from feeds.base import RssFeedParser


class HelpNetSecurityFeed(RssFeedParser):
    source_id = "help_net_security"
    feed_url = "https://www.helpnetsecurity.com/feed/"
