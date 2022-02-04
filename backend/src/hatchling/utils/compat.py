import json

# https://stackoverflow.com/a/33571117/5854007


def byteify_object(obj):
    json_text = json.dumps(obj)
    return _byteify(json.loads(json_text, object_hook=_byteify), ignore_dicts=True)


def _byteify(data, ignore_dicts=False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [_byteify(item, ignore_dicts=True) for item in data]
    if isinstance(data, dict) and not ignore_dicts:
        return {_byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True) for key, value in data.iteritems()}
    return data
