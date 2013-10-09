# LineProfiler

This plugin exposes a simple interface to
[line_profiler and kernprof](http://pythonhosted.org/line_profiler/)
inside Sublime Text 3.

## Configuration

 1. Install `line_profiler` and `kernprof.py` (see the above link).
 2. Update `LineProfiler.sublime-settings`:
   1. Set correct paths for `python` and `kernprof`.
   2. (Optional) Add any additional directories to `pythonpath`
   (i.e., if you set any in `.bashrc`, set them again here).
   Paths should be colon-separated.

## Usage

Add the `@profile` annotation to any functions you'd like to profile.
Then, run the plugin via the available bindings:
 * `ctrl-alt-shift-p`
 * right-click > Run line_profiler
 * Tools > Packages > Run line_profiler.

If successful, a scratch buffer will appear with your results.
If not, check the console (``ctrl-` ``)to see any error messages.

The profiler runs in a background process,
so Sublime will continue operating normally until a result is returned.

