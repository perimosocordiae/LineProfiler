# LineProfiler

This plugin exposes a simple interface to
[line_profiler and kernprof](http://pythonhosted.org/line_profiler/)
inside Sublime Text.

## Installation

LineProfiler is available via [Package Control](https://sublime.wbond.net/),
which is the easiest way to install it.
Alternatively, you can download this repository and place it in your `Packages` directory.

## Configuration

 1. Install `line_profiler` and `kernprof.py`.
     * Easiest way to install is `pip install --pre line_profiler`.
     * Also installable by downloading from [the line_profiler website](http://pythonhosted.org/line_profiler/).
 2. Optional: Update LineProfiler's settings
     * Accessible at (Preferences > Package Settings > LineProfiler > "Settings - User")

Available preferences are:
 
 * `python`: path to the Python binary you want to profile with.
   (Try using the result of `which python` if you're not sure.)
 * `kernprof`: path to the `kerprof.py` file you downloaded alongside the `line_profiler` module.
 * `pythonpath`: (Optional) colon-separated list of paths that will be appended to the start of the the default PYTHONPATH.
 * `poll_timeout_seconds`: (Optional) number of seconds to wait before killing the profiler.
   If you're profiling code that runs for longer than a minute, increase this value. 
 * `poll_sleep_seconds`: (Optional) number of seconds to sleep before polling the profiler for results.
   If you find the delay in getting profiler results too long, decrease this value.

## Usage

Add the `@profile` annotation to any functions you'd like to profile.
Then, run the plugin via the available bindings:
 * `ctrl-alt-shift-p`
 * right-click > "Run line_profiler"
 * Tools > Packages > "Run line_profiler"

If successful, a scratch buffer will appear with your results.
If not, check the console (``ctrl-` ``) to see any error messages.

The profiler runs in a background process,
so Sublime will continue operating normally until a result is returned.

## Example

Here's a simple way to try out LineProfiler and get familiar with the plugin.

Step 1: Open Sublime and write a simple Python file:

```python
def foo():
  for i in xrange(1000):
    bar = i**2
    baz = i*i

if __name__ == '__main__':
  foo()
```

Sure, it doesn't do much, but it'll run.
Be sure to tell Sublime that it's Python code,
either by saving it as a .py file, or selecting Python in the bottom bar.

Step 2: Add the `@profile` decorator to the `foo` function, like so:

```python
@profile
def foo():
```

(Everything else is unchanged.)

Step 3: Run LineProfiler, either from the Command Palette,
the right-click menu, or the keyboard shortcut.
The command is only available in Python mode, so check that first.

Step 4: Wait about a second, and then watch as the profile results appear in a new tab.
If all went well, you should see the lines of the `foo` function annotated with their run counts,
total time, and time per run:

```
function foo in file tmpev_rzr.py took 0.001248 s

Line #      Hits         Time  Per Hit   % Time  Line Contents
==============================================================
     2                                           @profile
     3                                           def foo():
     4      1001          372      0.4     29.8    for i in xrange(1000):
     5      1000          458      0.5     36.7      bar = i**2
     6      1000          418      0.4     33.5      baz = i*i
```

Some lines may be highlighted.
These are "hot spots" in your code, which take up a disproportionate amount of time.

If you don't see anything after a second,
check the console (``ctrl-` ``) to see what went wrong.
Often, the issue is a simple matter of setting the right paths in the user settings file.
