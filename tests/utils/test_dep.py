from hatch.utils.dep import resolve_extras


class TestResolveExtras:
    def test_no_extras(self):
        deps = ["requests>=2.0"]
        local_projects = {"my-app": {}}
        assert resolve_extras(deps, local_projects) == ["requests>=2.0"]

    def test_local_project_without_extras_excluded(self):
        deps = ["my-app", "requests>=2.0"]
        local_projects = {"my-app": {}}
        assert resolve_extras(deps, local_projects) == ["requests>=2.0"]

    def test_extra_expansion_no_marker(self):
        deps = ["my-app[cli]"]
        local_projects = {"my-app": {"cli": ["click>=8.0"]}}
        assert resolve_extras(deps, local_projects) == ["click>=8.0"]

    def test_extra_expansion_preserves_outer_marker(self):
        deps = ["my-app[win]; sys_platform == 'win32'"]
        local_projects = {"my-app": {"win": ["pywin32>=306"]}}
        resolved = resolve_extras(deps, local_projects)
        assert resolved == ['pywin32>=306; sys_platform == "win32"']

    def test_extra_expansion_combines_with_inner_marker(self):
        deps = ["my-app[win]; sys_platform == 'win32'"]
        local_projects = {"my-app": {"win": ["pywin32>=306; os_name == 'nt'"]}}
        resolved = resolve_extras(deps, local_projects)
        assert resolved == ['pywin32>=306; os_name == "nt" and sys_platform == "win32"']

    def test_extra_expansion_combines_disjunctive_markers(self):
        deps = ["my-app[win]; sys_platform == 'win32' or sys_platform == 'cygwin'"]
        local_projects = {"my-app": {"win": ["pywin32>=306; os_name == 'nt' or os_name == 'posix'"]}}
        resolved = resolve_extras(deps, local_projects)
        assert resolved == [
            'pywin32>=306; (os_name == "nt" or os_name == "posix") and (sys_platform == "win32" or sys_platform == "cygwin")'
        ]

    def test_nested_extras_preserves_marker(self):
        deps = ["my-app[dev]; sys_platform == 'win32'"]
        local_projects = {
            "my-app": {
                "dev": ["my-app[win]"],
                "win": ["pywin32>=306"],
            }
        }
        resolved = resolve_extras(deps, local_projects)
        assert resolved == ['pywin32>=306; sys_platform == "win32"']

    def test_nested_extras_combines_multiple_markers(self):
        deps = ["my-app[dev]; sys_platform == 'win32'"]
        local_projects = {
            "my-app": {
                "dev": ["my-app[win]; python_version >= '3.10'"],
                "win": ["pywin32>=306; os_name == 'nt'"],
            }
        }
        resolved = resolve_extras(deps, local_projects)
        assert resolved == ['pywin32>=306; os_name == "nt" and (python_version >= "3.10" and sys_platform == "win32")']

    def test_multiple_extras_in_requirement(self):
        deps = ["my-app[win,doc]; sys_platform == 'win32'"]
        local_projects = {
            "my-app": {
                "win": ["pywin32>=306"],
                "doc": ["sphinx>=7.0"],
            }
        }
        resolved = resolve_extras(deps, local_projects)
        assert set(resolved) == {
            'pywin32>=306; sys_platform == "win32"',
            'sphinx>=7.0; sys_platform == "win32"',
        }

    def test_cross_project_workspace_extras_preserves_marker(self):
        deps = ["member-a[all]; sys_platform == 'darwin'"]
        local_projects = {
            "member-a": {"all": ["member-b[gui]"]},
            "member-b": {"gui": ["pyobjc; platform_system == 'Darwin'"]},
        }
        resolved = resolve_extras(deps, local_projects)
        assert resolved == ['pyobjc; platform_system == "Darwin" and sys_platform == "darwin"']

    def test_undefined_extra_warning(self):
        warnings = []
        deps = ["my-app[missing]; sys_platform == 'win32'"]
        local_projects = {"my-app": {"existing": ["dep"]}}
        resolved = resolve_extras(deps, local_projects, warn=warnings.append)
        assert resolved == []
        assert len(warnings) == 1
        assert "my-app[missing]; sys_platform == 'win32'" in warnings[0]
        assert "missing" in warnings[0]
