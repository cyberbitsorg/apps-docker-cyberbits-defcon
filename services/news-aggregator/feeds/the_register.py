from feeds.base import RssFeedParser


class TheRegisterFeed(RssFeedParser):
    source_id = "the_register"
    feed_url = "https://www.theregister.com/security/headlines.atom"
