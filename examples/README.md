# Moulti example scripts

This directory contains example scripts that demonstrate various features and uses of Moulti.

Descriptions:
- debian-upgrade: assume the underlying host is Debian-based and upgrade it using apt
- many-buttons: display two steps with numerous buttons
- pass-concurrency: display 8 (actually `$MOULTI_PASS_CONCURRENCY`) steps running `ping localhost` concurrently
- progressbar: track the generation of 10 SSH keys using a progress bar
- python-checks: run linters on Moulti code; to be executed from the parent directory
- scoreboard: display the scores of two teams (home and guest) next to each other, along with a timer in the center of the screen; this unusual layout is achieved through `MOULTI_CUSTOM_CSS`
- social-preview: display 4 steps using toilet, ping and bat -- used to generate Moulti's social preview picture

## Compatibility matrix

|                  | Linux | macOS | FreeBSD | NetBSD | OpenBSD |
|------------------|-------|-------|---------|--------|---------|
| debian-upgrade   | ⚠️  [1]|  ❌   |   ❌    |   ❌   |   ❌    |
| many-buttons     | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |
| needle-haystack  | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |
| pass-concurrency | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |
| progressbar      | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |
| python-checks    | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |
| scoreboard       | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |
| social-preview   | ✅    |  ✅   |   ✅    |   ✅   |   ✅    |

[1] Debian-based distributions only

## Contributions

Contrib example scripts are welcome provided they pass the following check list:

- [ ] bash or zsh
- [ ] reasonable dependencies
- [ ] no significant `shellcheck` warning
- [ ] portability: contrib examples should run on at least two of the target platforms
- [ ] use `moulti_check_requirements()` to ensure all external tools are available
