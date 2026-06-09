# How to use Hatch environments from Emacs

-----

The [pyvenv](https://github.com/jorgenschaefer/pyvenv) package is
frequently used to manage virtual environments in Emacs (with
[elpy](https://github.com/jorgenschaefer/elpy) for instance).  To make
it easier to use with Hatch, you can add the following function to
your `.emacs` to add the command `hatch-activate`, which works like
`pyvenv-activate` but activates the default environment for the
current directory:

```lisp
(require 'subr-x)
(require 'pyvenv)
(defun hatch-activate (directory)
  "Activate the default hatch virtual environment for DIRECTORY"
  (interactive (list (read-directory-name "Activate for project: ")))
  (let ((expdir (expand-file-name directory))
        (default-directory directory))
    (let ((hatch-env
           (string-trim
            (shell-command-to-string "hatch env find"))))
      (pyvenv-activate hatch-env)
    )))
```
