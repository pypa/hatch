import os


def running_in_ci():
    for env_var in ('CI', 'GITHUB_ACTIONS'):
        if os.environ.get(env_var) in ('true', '1'):
            return True

    return False
