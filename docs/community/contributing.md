# Contributing

The usual process to make a contribution is to:

1. Check for existing related issues
2. Fork the repository and create a new branch
3. Make your changes
4. Make sure formatting, linting and tests passes.
5. Add tests if possible to cover the lines you added.
6. Commit, and send a Pull Request.

## AI Contributions 
We recognize that AI is now a tool in many people's toolbelt. 
As such contributions may use AI as long as the following guidelines are followed. 

1. You are responsible for the code that is generated. You should review the code before creating a PR. 
2. Keep PRs limited in scope, PRs are still reviewed by a human. 
3. Code should follow the conventions that are already in use in hatch's code base.
4. PR descriptions should be human written, this helps communication between contributor and maintainers.

### Autonomous Code Submissions 
We do not permit autonomous code submissions where an agent writes code and creates the PR. 
We require that there is a human in the loop. 

## Clone the repository

Clone the `hatch` repository, `cd` into it, and create a new branch for your contribution:

```bash
cd hatch
git switch -c add-my-contribution
```

## Run the tests

Run the test suite while developing:

```bash
hatch test
```

Run the test suite with coverage report:

```bash
hatch test --cover
```

Run the extended test suite with coverage:

```bash
hatch test --cover --all
```

## Lint

Run automated formatting:

```bash
hatch fmt
```

Run full linting and type checking:

```bash
hatch fmt --check
hatch run types:check
```

## Docs

Start the documentation in development:

```bash
hatch run docs:serve
```

Build and validate the documentation website:

```bash
hatch run docs:build-check
```