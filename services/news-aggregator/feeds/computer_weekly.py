from feeds.base import RssFeedParser


class ComputerWeeklyFeed(RssFeedParser):
    source_id = "computer_weekly"
    feed_url = "https://www.computerweekly.com/rss/IT-security.xml"
