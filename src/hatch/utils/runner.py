from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface


class ExecutionContext:
    def __init__(
        self,
        environment: EnvironmentInterface,
        *,
        shell_commands: list[str] | None = None,
        env_vars: dict[str, str] | None = None,
        force_continue: bool = False,
        show_code_on_error: bool = False,
        hide_commands: bool = False,
        source: str = 'cmd',
    ) -> None:
        self.env = environment
        self.shell_commands: list[str] = shell_commands or []
        self.env_vars: dict[str, str] = env_vars or {}
        self.force_continue = force_continue
        self.show_code_on_error = show_code_on_error
        self.hide_commands = hide_commands
        self.source = source

    def add_shell_command(self, command: str | list[str]) -> None:
        self.shell_commands.append(command if isinstance(command, str) else self.env.join_command_args(command))


def parse_matrix_variables(specs: tuple[str, ...]) -> dict[str, set[str]]:
    variables: dict[str, set[str]] = {}
    for spec in specs:
        variable, _, values = spec.partition('=')
        if variable == 'py':
            variable = 'python'

        if variable in variables:
            raise ValueError(variable)

        variables[variable] = set(values.split(',')) if values else set()

    return variables


def select_environments(
    environments: dict[str, dict[str, Any]],
    included_variables: dict[str, set[str]],
    excluded_variables: dict[str, set[str]],
):
    selected_environments = []
    for env_name, variables in environments.items():
        exclude = False
        for excluded_variable, excluded_values in excluded_variables.items():
            if excluded_variable not in variables:
                continue

            value = variables[excluded_variable]
            if not excluded_values or value in excluded_values:
                exclude = True
                break

        if exclude:
            continue

        for included_variable, included_values in included_variables.items():
            if included_variable not in variables:
                exclude = True
                break

            value = variables[included_variable]
            if included_values and value not in included_values:
                exclude = True
                break

        if not exclude:
            selected_environments.append(env_name)

    return selected_environments
