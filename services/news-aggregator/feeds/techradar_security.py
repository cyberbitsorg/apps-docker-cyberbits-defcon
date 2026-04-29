from feeds.base import RssFeedParser


class TechRadarSecurityFeed(RssFeedParser):
    source_id = "techradar_security"
    feed_url = "https://www.techradar.com/feeds/tag/security"
