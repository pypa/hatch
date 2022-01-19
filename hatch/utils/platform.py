from __future__ import annotations

import os
import sys


def normalize_platform_name(platform_name):
    platform_name = platform_name.lower()
    return 'macos' if platform_name == 'darwin' else platform_name


class Platform:
    def __init__(self, display_func=print):
        self.__display_func = display_func

        # Lazy load modules that either take multiple milliseconds to import or are not used on all platforms
        self.__shlex = None
        self.__shutil = None
        self.__subprocess = None

        # Lazily loaded constants
        self.__default_shell = None
        self.__format_file_uri = None
        self.__join_command_args = None
        self.__name = None

        # Whether or not an interactive status is being displayed
        self.displaying_status = False

    def format_for_subprocess(self, command: str | list[str], *, shell: bool):
        """
        Format the given command in a cross-platform manner for immediate consumption by subprocess utilities.
        """
        if self.windows:
            # Manually locate executables on Windows to avoid multiple cases in which `shell=True` is required:
            #
            # - If the `PATH` environment variable has been modified, see: https://bugs.python.org/issue8557
            # - Executables that do not have the extension `.exe`, see:
            #   https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw
            if not shell and not isinstance(command, str):
                executable = command[0]
                new_command = [self._shutil.which(executable) or executable]
                new_command.extend(command[1:])
                return new_command
        else:
            if not shell and isinstance(command, str):
                return self._shlex.split(command)

        return command

    def exit_with_code(self, code):
        return sys.exit(code)

    def _run_command_integrated(self, command: str | list[str], shell=False, **kwargs):
        with self.capture_process(command, shell=shell, **kwargs) as process:
            for line in self.stream_process_output(process):
                self.__display_func(line, end='')

            stdout, stderr = process.communicate()

        return self._subprocess.CompletedProcess(process.args, process.poll(), stdout, stderr)

    def run_command(self, command: str | list[str], shell=False, **kwargs):
        """
        Equivalent to the standard library's
        [subprocess.run](https://docs.python.org/3/library/subprocess.html#subprocess.run),
        with the command first being
        [properly formatted](utilities.md#hatch.utils.platform.Platform.format_for_subprocess).
        """
        if self.displaying_status and not kwargs.get('capture_output'):
            return self._run_command_integrated(command, shell=shell, **kwargs)

        return self._subprocess.run(self.format_for_subprocess(command, shell=shell), shell=shell, **kwargs)

    def check_command(self, command: str | list[str], shell=False, **kwargs):
        """
        Equivalent to [run_command](utilities.md#hatch.utils.platform.Platform.run_command),
        but non-zero exit codes will gracefully end program execution.
        """
        process = self.run_command(command, shell=shell, **kwargs)
        if process.returncode:
            self.exit_with_code(process.returncode)

        return process

    def check_command_output(self, command: str | list[str], shell=False, **kwargs) -> str:
        """
        Equivalent to the output from the process returned by
        [capture_process](utilities.md#hatch.utils.platform.Platform.capture_process),
        but non-zero exit codes will gracefully end program execution.
        """
        with self.capture_process(command, shell=shell, **kwargs) as process:
            stdout, _ = process.communicate()

        if process.returncode:
            self.__display_func(stdout.decode('utf-8'))
            self.exit_with_code(process.returncode)

        return stdout.decode('utf-8')

    def capture_process(self, command: str | list[str], shell=False, **kwargs):
        """
        Equivalent to the standard library's
        [subprocess.Popen](https://docs.python.org/3/library/subprocess.html#subprocess.Popen),
        with all output captured by `stdout` and the command first being
        [properly formatted](utilities.md#hatch.utils.platform.Platform.format_for_subprocess).
        """
        return self._subprocess.Popen(
            self.format_for_subprocess(command, shell=shell),
            shell=shell,
            stdout=self._subprocess.PIPE,
            stderr=self._subprocess.STDOUT,
            **kwargs,
        )

    @staticmethod
    def stream_process_output(process):
        # To avoid blocking never use a pipe's file descriptor iterator. See https://bugs.python.org/issue3907
        for line in iter(process.stdout.readline, b''):
            yield line.decode('utf-8')

    @property
    def default_shell(self):
        """
        Returns the default shell of the system.

        On Windows systems the `COMSPEC` environment variable will be used, defaulting to `cmd`.
        Otherwise the `SHELL` environment variable will be used, defaulting to `bash`.
        """
        if self.__default_shell is None:
            if self.windows:
                self.__default_shell = os.environ.get('COMSPEC', 'cmd')
            else:
                self.__default_shell = os.environ.get('SHELL', 'bash')

        return self.__default_shell

    @property
    def join_command_args(self):
        if self.__join_command_args is None:
            if self.windows:
                self.__join_command_args = self._subprocess.list2cmdline
            else:
                try:
                    self.__join_command_args = self._shlex.join
                except AttributeError:
                    self.__join_command_args = lambda command_args: ' '.join(map(self._shlex.quote, command_args))

        return self.__join_command_args

    @property
    def format_file_uri(self):
        if self.__format_file_uri is None:
            if self.windows:
                self.__format_file_uri = lambda p: f'file:///{p}'.replace('\\', '/')
            else:
                self.__format_file_uri = lambda p: f'file://{p}'

        return self.__format_file_uri

    @property
    def windows(self):
        """
        Indicates whether Hatch is running on Windows.
        """
        return self.name == 'windows'

    @property
    def macos(self):
        """
        Indicates whether Hatch is running on macOS.
        """
        return self.name == 'macos'

    @property
    def linux(self):
        """
        Indicates whether Hatch is running on neither Windows nor macOS.
        """
        return not (self.windows or self.macos)

    def exit_with_command(self, command: list[str]):
        """
        Run the given command and exit with its exit code. On non-Windows systems, this uses the standard library's
        [os.execvp](https://docs.python.org/3/library/os.html#os.execvp).
        """
        if self.windows:
            process = self.run_command(command)
            self.exit_with_code(process.returncode)
        else:
            return os.execvp(command[0], command)

    @property
    def name(self):
        """
        One of the following:

        - `linux`
        - `windows`
        - `macos`
        """
        if self.__name is None:
            import platform

            self.__name = normalize_platform_name(platform.system())

        return self.__name

    @property
    def _subprocess(self):
        if self.__subprocess is None:
            import subprocess as subprocess_

            self.__subprocess = subprocess_

        return self.__subprocess

    @property
    def _shlex(self):
        if self.__shlex is None:
            import shlex as shlex_

            self.__shlex = shlex_

        return self.__shlex

    @property
    def _shutil(self):
        if self.__shutil is None:
            import shutil as shutil_

            self.__shutil = shutil_

        return self.__shutil
