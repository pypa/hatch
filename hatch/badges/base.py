from collections import OrderedDict

try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode


class Badge:
    def __init__(self, image, target, param_pairs=None):
        self.image = image
        self.target = target

        if param_pairs:
            self.image += '?' + urlencode(OrderedDict(param_pairs))
