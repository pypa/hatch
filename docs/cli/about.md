# About

-----

## Verbosity

The amount of displayed output is controlled solely by the `-v`/`--verbose` (environment variable `HATCH_VERBOSE`) and  `-q`/`--quiet` (environment variable `HATCH_QUIET`) [root options](reference.md#hatch).

The levels are documented [here](../config/hatch.md#terminal).

## Project awareness

No matter the [mode](../config/hatch.md#mode), Hatch will always change to the project's root directory for [entering](../environment.md#entering-environments) or [running commands](../environment.md#command-execution) in environments.

## Tab completion

Completion is achieved by saving a script and then executing it as a part of your shell's startup sequence.

Afterward, you'll need to start a new shell in order for the changes to take effect.

=== "Bash"
    Save the script somewhere:

    ```console
    _HATCH_COMPLETE=bash_source hatch > ~/.hatch-complete.bash
    ```

    Source the file in `~/.bashrc` (or `~/.bash_profile` if on macOS):

    ```bash
    . ~/.hatch-complete.bash
    ```

=== "Z shell"
    Save the script somewhere:

    ```console
    _HATCH_COMPLETE=zsh_source hatch > ~/.hatch-complete.zsh
    ```

    Source the file in `~/.zshrc`:

    ```zsh
    . ~/.hatch-complete.zsh
    ```

=== "fish"
    Save the script in `~/.config/fish/completions`:

    ```console
    _HATCH_COMPLETE=fish_source hatch > ~/.config/fish/completions/hatch.fish
    ```
