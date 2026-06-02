# Contributing

The usual process to make a contribution is to:

1. Check for existing related issues
2. Fork the repository and create a new branch
3. Make your changes
4. Make sure formatting, linting and tests passes.
5. Add tests if possible to cover the lines you added.
6. Commit, and send a Pull Request.

## AI Contributions 
* All AI usage in any form must be disclosed. You must state the tool you used (e.g. Claude Code, Cursor, Amp) along with the extent that the work was AI-assisted.

* The human-in-the-loop must fully understand all code. If you can't explain what your changes do and how they interact with the greater system without the aid of AI tools, do not contribute to this project.

* Issues and discussions can use AI assistance but must have a full human-in-the-loop. This means that any content generated with AI must have been reviewed and edited by a human before submission. AI is very good at being overly verbose and including noise that distracts from the main point. Humans must do their research and trim this down.


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

Run automated formatting and linting fixes:

```bash
hatch check --fix
```

Run all checks (linting, formatting, type checking):

```bash
hatch check
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