def test_default_scrubbed(hatch, config_file, helpers, default_cache_dir, default_data_dir):
    config_file.model.project = 'foo'
    config_file.model.publish['index']['auth'] = 'bar'
    config_file.save()

    result = hatch('config', 'show')

    default_cache_directory = str(default_cache_dir).replace('\\', '\\\\')
    default_data_directory = str(default_data_dir).replace('\\', '\\\\')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        mode = "local"
        project = "foo"
        shell = ""

        [dirs]
        project = []
        python = "isolated"
        data = "{default_data_directory}"
        cache = "{default_cache_directory}"

        [dirs.env]

        [projects]

        [template]
        name = "Foo Bar"
        email = "foo@bar.baz"

        [template.licenses]
        headers = true
        default = [
            "MIT",
        ]

        [template.plugins.default]
        tests = true
        ci = false
        src-layout = false

        [terminal.styles]
        info = "bold"
        success = "bold cyan"
        error = "bold red"
        warning = "bold yellow"
        waiting = "bold magenta"
        debug = "bold"
        spinner = "simpleDotsScrolling"
        """
    )


def test_reveal(hatch, config_file, helpers, default_cache_dir, default_data_dir):
    config_file.model.project = 'foo'
    config_file.model.publish['index']['auth'] = 'bar'
    config_file.save()

    result = hatch('config', 'show', '-a')

    default_cache_directory = str(default_cache_dir).replace('\\', '\\\\')
    default_data_directory = str(default_data_dir).replace('\\', '\\\\')

    assert result.exit_code == 0, result.output
    assert result.output == helpers.dedent(
        f"""
        mode = "local"
        project = "foo"
        shell = ""

        [dirs]
        project = []
        python = "isolated"
        data = "{default_data_directory}"
        cache = "{default_cache_directory}"

        [dirs.env]

        [projects]

        [publish.index]
        repo = "main"
        auth = "bar"

        [template]
        name = "Foo Bar"
        email = "foo@bar.baz"

        [template.licenses]
        headers = true
        default = [
            "MIT",
        ]

        [template.plugins.default]
        tests = true
        ci = false
        src-layout = false

        [terminal.styles]
        info = "bold"
        success = "bold cyan"
        error = "bold red"
        warning = "bold yellow"
        waiting = "bold magenta"
        debug = "bold"
        spinner = "simpleDotsScrolling"
        """
    )
