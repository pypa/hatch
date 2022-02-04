import os
import pickle
import sys


class InvokedApplication(object):
    def display_info(self, *args, **kwargs):
        send_app_command('display_info', *args, **kwargs)

    def display_waiting(self, *args, **kwargs):
        send_app_command('display_waiting', *args, **kwargs)

    def display_success(self, *args, **kwargs):
        send_app_command('display_success', *args, **kwargs)

    def display_warning(self, *args, **kwargs):
        send_app_command('display_warning', *args, **kwargs)

    def display_error(self, *args, **kwargs):
        send_app_command('display_error', *args, **kwargs)

    def display_debug(self, *args, **kwargs):
        send_app_command('display_debug', *args, **kwargs)

    def display_mini_header(self, *args, **kwargs):
        send_app_command('display_mini_header', *args, **kwargs)

    def abort(self, *args, **kwargs):
        send_app_command('abort', *args, **kwargs)
        sys.exit(kwargs.get('code', 1))

    def get_safe_application(self):
        return SafeApplication(self)


class Application(object):
    """
    The way output is displayed can be [configured](../config/hatch.md#terminal) by users.
    """

    def __init__(self):
        self.__verbosity = int(os.environ.get('HATCH_VERBOSE', '0')) - int(os.environ.get('HATCH_QUIET', '0'))

    def display_info(self, message='', **kwargs):
        """
        Meant to be used for messages conveying basic information.
        """
        if self.__verbosity >= 0:
            print(message)

    def display_waiting(self, message='', **kwargs):
        """
        Meant to be used for messages shown before potentially time consuming operations.
        """
        if self.__verbosity >= 0:
            print(message)

    def display_success(self, message='', **kwargs):
        """
        Meant to be used for messages indicating some positive outcome.
        """
        if self.__verbosity >= 0:
            print(message)

    def display_warning(self, message='', **kwargs):
        """
        Meant to be used for messages conveying important information.
        """
        if self.__verbosity >= -1:
            print(message)

    def display_error(self, message='', **kwargs):
        """
        Meant to be used for messages indicating some unrecoverable error.
        """
        if self.__verbosity >= -2:
            print(message)

    def display_debug(self, message='', level=1, **kwargs):
        """
        Meant to be used for messages that are not useful for most user experiences.
        The `level` option must be between 1 and 3 (inclusive).
        """
        if not 1 <= level <= 3:
            raise ValueError('Debug output can only have verbosity levels between 1 and 3 (inclusive)')
        elif self.__verbosity >= level:
            print(message)

    def display_mini_header(self, message='', **kwargs):
        if self.__verbosity >= 0:
            print('[{}]'.format(message))

    def abort(self, message='', code=1, **kwargs):
        """
        Terminate the program with the given return code.
        """
        if message and self.__verbosity >= -2:
            print(message)

        sys.exit(code)

    def get_safe_application(self):
        return SafeApplication(self)


class SafeApplication:
    def __init__(self, app):
        self.abort = app.abort
        self.display_info = app.display_info
        self.display_error = app.display_error
        self.display_success = app.display_success
        self.display_waiting = app.display_waiting
        self.display_warning = app.display_warning
        self.display_debug = app.display_debug
        self.display_mini_header = app.display_mini_header


if sys.version_info[0] >= 3:

    def format_app_command(method, *args, **kwargs):
        # TODO: increase protocol version when Python 2 support is dropped
        procedure = pickle.dumps((method, args, kwargs), 2)

        return '__HATCH__:{}'.format(''.join('%02x' % i for i in procedure))

else:

    def format_app_command(method, *args, **kwargs):
        procedure = pickle.dumps((method, args, kwargs), 2)

        return '__HATCH__:{}'.format(''.join('%02x' % ord(c) for c in procedure))


def send_app_command(method, *args, **kwargs):
    _send_app_command(format_app_command(method, *args, **kwargs))


def _send_app_command(command):
    print(command)
