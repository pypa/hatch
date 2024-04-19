# How use Hatch environments from VS Code

-----

## Global setup

Visual Studio Code announced support for [Hatch environment discovery][] in vscode-python’s [2024.4 release][].

For it to work, you should [install Hatch][] globally. If you used the GUI installers on Windows or MacOS, or your system package manager on e.g. Arch Linux or Fedora Linux this should be taken care of.

<details>
<summary>If you used e.g. `pipx install Hatch`, please make sure you set your PATH correctly.</summary>

If you cannot install Hatch system-wide, you might need to add `$HOME/.local/bin` to your PATH environment variable *for your graphical session*, not just your terminal. Check like this:

```console
$ pgrep bin/code  # or some other graphical application
1234
$ cat /proc/1234/environ | tr '\0' '\n' | grep -E '^PATH='
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
```

If the the directory is not in there, you need to add it in your session startup script, in a way that depends on your desktop environment:

- [KDE Plasma](https://userbase.kde.org/Session_Environment_Variables)
- [GNOME](https://help.ubuntu.com/community/EnvironmentVariables#Session-wide_environment_variables)

</details>

## Per-project setup

1. Make Hatch install the project and its dependencies to an environment using [`hatch env create`][].

2. Select your as an interpreter using <kbd>Python: Select Interpreter</kbd> command

   <img width="611" alt="image" src="https://github.com/microsoft/vscode-python/assets/291575/a3414d81-f585-4c77-a2b4-c36163bf94b5">

3. You should now be able use the environment, e.g. you could open a new terminal: If you have the `python.terminal.activateEnvironment` setting set to `true`, the environment should be activated. Or you press the “play” button to run a file in the environment:

   <img width="512" alt="image" src="https://github.com/microsoft/vscode-python/assets/291575/808ae1f2-a13a-4ddc-a747-d4b347974555">

[Hatch environment discovery]: https://code.visualstudio.com/updates/v1_88#_hatch-environment-discovery
[2024.4 release]: https://github.com/microsoft/vscode-python/releases/tag/v2024.4.0
[install Hatch]: ../../install.md
[`hatch env create`]: ../../cli/reference.md#hatch-env-create
