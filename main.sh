#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

PURPLE="\033[1;35m"
RESET="\033[0m"

if [[ "${RUNNER_OS}" == "Windows" ]]; then
  SEP="\\"
else
  SEP="/"
fi
INSTALL_PATH="${RUNNER_TOOL_CACHE}${SEP}.hatch"

curl_opts=(
  --fail              # fail on HTTP errors (>=400), prevents saving an error page
  --silent            # no progress meter or extra output
  --show-error        # but still show errors (important for debugging)
  --location          # follow redirects
  --retry 2           # retry N more times on transient errors
  --retry-connrefused # also if connection is refused (CDN saturation cases)
)

install_hatch() {
  mkdir -p "${INSTALL_PATH}"
  archive="${INSTALL_PATH}${SEP}$1"

  echo -e "${PURPLE}Downloading Hatch ${VERSION}${RESET}\n"
  if [[ "${VERSION}" == "latest" ]]; then
    curl "${curl_opts[@]}" -o "${archive}" "https://github.com/pypa/hatch/releases/latest/download/$1"
  else
    curl "${curl_opts[@]}" -o "${archive}" "https://github.com/pypa/hatch/releases/download/hatch-v${VERSION}/$1"
  fi

  if [[ "${archive}" =~ \.zip$ ]]; then
    if [[ "${RUNNER_OS}" == "Windows" ]]; then
      7z -bso0 -bsp0 x "${archive}" -o"${INSTALL_PATH}"
    else
      unzip "${archive}" -d "${INSTALL_PATH}"
    fi
  else
    tar -xzf "${archive}" -C "${INSTALL_PATH}"
  fi
  rm "${archive}"

  echo -e "${PURPLE}Installing Hatch ${VERSION}${RESET}"
  "${INSTALL_PATH}${SEP}hatch" --version
  "${INSTALL_PATH}${SEP}hatch" self cache dist --remove

  echo "${INSTALL_PATH}" >> "${GITHUB_PATH}"
}

fallback_install_hatch() {
  echo -e "${PURPLE}Installing Hatch ${VERSION}${RESET}"
  if [[ "${VERSION}" == "latest" ]]; then
    pipx install --pip-args=--upgrade hatch
  else
    pipx install "hatch==${VERSION}"
  fi

  hatch --version
}

if [[ "${RUNNER_OS}" == "Linux" ]]; then
  if [[ "${RUNNER_ARCH}" == "X64" ]]; then
    install_hatch "hatch-x86_64-unknown-linux-gnu.tar.gz"
  elif [[ "${RUNNER_ARCH}" == "ARM64" ]]; then
    install_hatch "hatch-aarch64-unknown-linux-gnu.tar.gz"
  else
    fallback_install_hatch
  fi
elif [[ "${RUNNER_OS}" == "Windows" ]]; then
  if [[ "${RUNNER_ARCH}" == "X64" ]]; then
    install_hatch "hatch-x86_64-pc-windows-msvc.zip"
  else
    fallback_install_hatch
  fi
elif [[ "${RUNNER_OS}" == "macOS" ]]; then
  if [[ "${RUNNER_ARCH}" == "ARM64" ]]; then
    install_hatch "hatch-aarch64-apple-darwin.tar.gz"
  elif [[ "${RUNNER_ARCH}" == "X64" ]]; then
    install_hatch "hatch-x86_64-apple-darwin.tar.gz"
  else
    fallback_install_hatch
  fi
else
  fallback_install_hatch
fi
