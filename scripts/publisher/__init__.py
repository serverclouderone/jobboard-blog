# Publisher — jobboard-blog
from scripts.publisher.cross_poster import CrossPoster
from scripts.publisher.hugo_publisher import publish

__all__ = [
    "publish",
    "CrossPoster",
]
