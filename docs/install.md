# Installation

-----

## Installers

=== "macOS"
    === "GUI installer"
        1. In your browser, download the `.pkg` file: [hatch-<HATCH_LATEST_VERSION>.pkg](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>.pkg)
        2. Run your downloaded file and follow the on-screen instructions.
        3. Restart your terminal.
        4. To verify that the shell can find and run the `hatch` command in your `PATH`, use the following command.

            ```
            $ hatch --version
            <HATCH_LATEST_VERSION>
            ```
    === "Command line installer"
        1. Download the file using the `curl` command. The `-o` option specifies the file name that the downloaded package is written to. In this example, the file is written to `hatch-<HATCH_LATEST_VERSION>.pkg` in the current directory.

            ```
            curl -o hatch-<HATCH_LATEST_VERSION>.pkg https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>.pkg
            ```
        2. Run the standard macOS [`installer`](https://ss64.com/osx/installer.html) program, specifying the downloaded `.pkg` file as the source. Use the `-pkg` parameter to specify the name of the package to install, and the `-target /` parameter for the drive in which to install the package. The files are installed to `/usr/local/hatch`, and an entry is created at `/etc/paths.d/hatch` that instructs shells to add the `/usr/local/hatch` directory to. You must include sudo on the command to grant write permissions to those folders.

            ```
            sudo installer -pkg ./hatch-<HATCH_LATEST_VERSION>.pkg -target /
            ```
        3. Restart your terminal.
        4. To verify that the shell can find and run the `hatch` command in your `PATH`, use the following command.

            ```
            $ hatch --version
            <HATCH_LATEST_VERSION>
            ```

=== "Windows"
    === "GUI installer"
        1. In your browser, download one the `.msi` files:
              - [hatch-<HATCH_LATEST_VERSION>-x64.msi](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x64.msi)
              - [hatch-<HATCH_LATEST_VERSION>-x86.msi](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x86.msi)
        2. Run your downloaded file and follow the on-screen instructions.
        3. Restart your terminal.
        4. To verify that the shell can find and run the `hatch` command in your `PATH`, use the following command.

            ```
            $ hatch --version
            <HATCH_LATEST_VERSION>
            ```
    === "Command line installer"
        1. Download and run the installer using the standard Windows [`msiexec`](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/msiexec) program, specifying one of the `.msi` files as the source. Use the `/passive` and `/i` parameters to request an unattended, normal installation.

            === "x64"
                ```
                msiexec /passive /i https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x64.msi
                ```
        2. Restart your terminal.
        3. To verify that the shell can find and run the `hatch` command in your `PATH`, use the following command.

            ```
            $ hatch --version
            <HATCH_LATEST_VERSION>
            ```

## Standalone binaries

After downloading the archive corresponding to your platform and architecture, extract the binary to a directory that is on your PATH and rename to `hatch`.

=== "Linux"
    - [hatch-<HATCH_LATEST_VERSION>-aarch64-unknown-linux-gnu.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-aarch64-unknown-linux-gnu.tar.gz)
    - [hatch-<HATCH_LATEST_VERSION>-x86_64-unknown-linux-gnu.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x86_64-unknown-linux-gnu.tar.gz)
    - [hatch-<HATCH_LATEST_VERSION>-x86_64-unknown-linux-musl.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x86_64-unknown-linux-musl.tar.gz)
    - [hatch-<HATCH_LATEST_VERSION>-i686-unknown-linux-gnu.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-i686-unknown-linux-gnu.tar.gz)
    - [hatch-<HATCH_LATEST_VERSION>-powerpc64le-unknown-linux-gnu.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-powerpc64le-unknown-linux-gnu.tar.gz)

=== "macOS"
    - [hatch-<HATCH_LATEST_VERSION>-aarch64-apple-darwin.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-aarch64-apple-darwin.tar.gz)
    - [hatch-<HATCH_LATEST_VERSION>-x86_64-apple-darwin.tar.gz](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x86_64-apple-darwin.tar.gz)

=== "Windows"
    - [hatch-<HATCH_LATEST_VERSION>-x86_64-pc-windows-msvc.zip](https://github.com/pypa/hatch/releases/download/hatch-v<HATCH_LATEST_VERSION>/hatch-<HATCH_LATEST_VERSION>-x86_64-pc-windows-msvc.zip)

## pip

Hatch is available on PyPI and can be installed with [pip](https://pip.pypa.io).

```
pip install hatch
```

!!! warning
    This method modifies the Python environment in which you choose to install. Consider instead using [pipx](#pipx) to avoid dependency conflicts.

## pipx

[pipx](https://github.com/pypa/pipx) allows for the global installation of Python applications in isolated environments.

```
pipx install hatch
```

## Homebrew

See the [formula](https://formulae.brew.sh/formula/hatch) for more details.

```
brew install hatch
```

## Conda

See the [feedstock](https://github.com/conda-forge/hatch-feedstock) for more details.

```
conda install -c conda-forge hatch
```

or with [mamba](https://github.com/mamba-org/mamba):

```
mamba install hatch
```

!!! warning
    This method modifies the Conda environment in which you choose to install. Consider instead using [pipx](#pipx) or [condax](https://github.com/mariusvniekerk/condax) to avoid dependency conflicts.

## MacPorts

See the [port](https://ports.macports.org/port/hatch/) for more details.

```
sudo port install hatch
```

## Fedora

The minimum supported version is 37, currently in development as [Rawhide](https://docs.fedoraproject.org/en-US/releases/rawhide/).

```
sudo dnf install hatch
```

## Void Linux

```
xbps-install hatch
```

## Build system availability

Hatchling is Hatch's [build backend](config/build.md#build-system) which you will never need to install manually. See its [changelog](history/hatchling.md) for version information.

[![Packaging status](https://repology.org/badge/vertical-allrepos/hatchling.svg){ loading=lazy .off-glb }](https://repology.org/project/hatchling/versions)
