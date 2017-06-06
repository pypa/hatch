from hatch.utils import normalize_package_url
from hatch.badges.base import Badge


class CodecovBadge(Badge):
    def __init__(self, package_url, style=None):
        normalized_url = normalize_package_url(package_url)
        if normalized_url.startswith('github'):
            abbr_url = normalized_url.replace('github', 'gh', count=1)
        elif normalized_url.startswith('bitbucket'):
            abbr_url = normalized_url.replace('bitbucket', 'bb', count=1)
        else:
            abbr_url = normalized_url

        super(CodecovBadge, self).__init__(
            'https://img.shields.io/codecov/c/{}/master.svg'.format(normalized_url),
            'https://codecov.io/{}'.format(abbr_url),
            [('style', style)] if style else None
        )
