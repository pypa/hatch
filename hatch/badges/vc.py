from hatch.badges.base import Badge


class TravisBadge(Badge):
    def __init__(self, package_name, username, style=None):
        super(TravisBadge, self).__init__(
            'https://img.shields.io/travis/{}/{}/master.svg'.format(username, package_name),
            'https://travis-ci.org/{}/{}'.format(username, package_name),
            [('style', style)] if style else None
        )
