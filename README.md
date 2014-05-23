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
If not, check the console (``ctrl-` ``)to see any error messages.

The profiler runs in a background process,
so Sublime will continue operating normally until a result is returned.

