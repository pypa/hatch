from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from hatch.env.plugin.interface import EnvironmentInterface


class ExecutionContext:
    def __init__(self, environment: EnvironmentInterface) -> None:
        self.env = environment

        self.args: list[str] = []
        self.env_vars: dict[str, str] = {}


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
        included = set(variables)
        excluded = set()

        for variable, value in variables.items():
            if variable in excluded_variables:
                excluded_values = excluded_variables[variable]
                if not excluded_values or value in excluded_values:
                    excluded.add(variable)
                    break

            if included_variables:
                if variable not in included_variables:
                    included.remove(variable)
                else:
                    included_values = included_variables[variable]
                    if included_values and value not in included_values:
                        included.remove(variable)

        if included and not excluded:
            selected_environments.append(env_name)

    return selected_environments
