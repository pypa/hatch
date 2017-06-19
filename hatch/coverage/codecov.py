from hatch.structures import File

TEMPLATE = """\
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
        super(Codecov, self).__init__('.codecov.yml', TEMPLATE)
        self.package = 'codecov'
        self.command = 'codecov'
