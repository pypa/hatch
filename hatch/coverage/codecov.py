from hatch.structures import File

BASE = """\
comment: false
coverage:
    status:
        patch:
            default:
                target: '100'
        project:
            default:
                target: '100'
"""


class Codecov(File):
    def __init__(self):
        super(Codecov, self).__init__('.codecov.yml', BASE)
        self.package = 'codecov'
        self.command = 'codecov'
