import json

from hatch.utils.fs import Path


def get_auth(app, username, options, repo, repo_config) -> tuple[bool, str]:
    if 'auth' in options:
        return False, options['auth']

    auth_token = repo_config.get('auth', '')
    if auth_token:
        return False, auth_token

    import keyring

    auth_token = keyring.get_password(repo, username)
    if auth_token is not None:
        return False, auth_token

    if options['no_prompt']:
        app.abort('Missing required option: auth')

    return True, app.prompt('Enter your credentials', hide_input=True)


def get_user(app, cached_user_file, options, repo, repo_config) -> tuple[bool, str]:
    if 'user' in options:
        return False, options['user']

    username = repo_config.get('user', '')
    if username:
        return False, username

    username = cached_user_file.get_user(repo)
    if username is not None:
        return False, username

    if options['no_prompt']:
        app.abort('Missing required option: user')

    return True, app.prompt('Enter your username')


class CachedUserFile:
    def __init__(self, cache_dir: Path):
        self.path = cache_dir / 'previous_working_users.json'
        self._data = None

    def get_user(self, repo: str):
        return self.data.get(repo)

    def set_user(self, repo: str, user: str):
        self.data[repo] = user
        self.path.ensure_parent_dir_exists()
        self.path.write_text(json.dumps(self.data))

    @property
    def data(self):
        if self._data is None:
            if not self.path.is_file():
                self._data = {}
            else:
                contents = self.path.read_text()
                if not contents:  # no cov
                    self._data = {}
                else:
                    self._data = json.loads(contents)

        return self._data
