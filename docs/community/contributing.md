# Contributing

The usual process to make a contribution is to:

1. Check for existing related issues
2. Fork the repository and create a new branch
3. Make your changes
4.  Make sure formatting, linting and tests passes.
5. Add tests if possible to cover the lines you added.
6. Commit, and send a Pull Request.

## Clone the repository

Clone the `hatch` repository, `cd` into it, and create a new branch for your contribution:

```bash
cd hatch
git checkout -b add-my-contribution
```

## Run the tests

Run the test suite while developing:

```bash
hatch run dev
```

Run the test suite with coverage report:

```bash
hatch run cov
```

Run the extended test suite with coverage:

```bash
hatch run full
```

## Lint

Run automated formatting:

```bash
hatch run lint:fmt
```

Run full linting and type checking:

```bash
hatch run lint:all
```

## Docs

Start the documentation in development:

```bash
hatch run docs:serve
```

Build and validate the documentation website:

```bash
hatch run build-check
```