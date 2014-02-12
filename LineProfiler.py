from __future__ import print_function
import math
import os
import sublime
import sublime_plugin
import subprocess
import sys
import tempfile
import time
import threading

SETTINGS = None


def plugin_loaded():
  global SETTINGS
  SETTINGS = sublime.load_settings('LineProfiler.sublime-settings')
  if SETTINGS and SETTINGS.get('python') is not None:
    print('Loaded settings for LineProfiler')
  else:
    print('Error loading settings for LineProfiler')

if sys.version_info[0] == 2:
  sublime.set_timeout(plugin_loaded, 0)


class LineProfilerCommand(sublime_plugin.TextCommand):
  def is_visible(self):
    return self.is_enabled()

  def is_enabled(self):
    return 'source.python' in self.view.scope_name(0)

  def run(self, edit):
    if not self.is_enabled():
      return

    # set up paths
    fname = self.view.file_name()
    is_tmpfile = False
    env = os.environ.copy()
    pythonpath = SETTINGS.get('pythonpath','')
    if fname is None:
      env['PYTHONPATH'] = pythonpath
      cwd = None
    else:
      cwd = os.path.dirname(fname)
      env['PYTHONPATH'] = cwd + os.pathsep + pythonpath

    # write the file if it's not saved right now
    if fname is None or self.view.is_dirty():
      contents = self.view.substr(sublime.Region(0, self.view.size()))
      with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as fh:
        fh.write(contents.encode('UTF-8'))
        fname = fh.name
      is_tmpfile = True

    # run kernprof with the correct paths
    python = SETTINGS.get('python','python')
    kernprof = SETTINGS.get('kernprof','kernprof.py')
    p = subprocess.Popen([python,kernprof,'-lbv','-o','/dev/null',fname],
                         env=env, cwd=cwd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)

    # set up the output catcher thread
    window = self.view.window()
    if not is_tmpfile:
      fname = None
    poll_timeout = SETTINGS.get('poll_timeout_seconds', 60)
    poll_sleep = SETTINGS.get('poll_sleep_seconds', 1)
    threading.Thread(target=read_output,
                     args=(window, p, fname, poll_timeout, poll_sleep)).start()


class LineProfilerOutputCommand(sublime_plugin.TextCommand):
  def run(self, edit, profile_data=None, hot_lines=None):
    if profile_data is None or hot_lines is None:
      print('This command should only be called by line_profiler')
      return
    self.view.insert(edit,0, profile_data)
    hot_regions = []
    from_idx = 0
    for line in hot_lines:
      r = self.view.find(line, from_idx, sublime.LITERAL)
      from_idx = r.end()
      hot_regions.append(r)
    self.view.add_regions('hot_lines', hot_regions,'comment','bookmark')
    self.view.set_read_only(True)


def read_output(window, p, fname, poll_timeout, poll_sleep):
  sublime.set_timeout(lambda: sublime.status_message('Profiling...'), 0)
  # poll for results
  tic = time.time()
  while p.poll() is None:
    if time.time() - tic > poll_timeout:
      msg = 'Profiler timed out after %f s' % (time.time() - tic)
      print(msg)
      sublime.set_timeout(lambda: sublime.status_message(msg), 0)
      p.kill()
      return
    time.sleep(poll_sleep)
    sublime.set_timeout(lambda: sublime.status_message('Profiling...'), 0)
  sublime.set_timeout(lambda: sublime.status_message('Profile complete.'), 0)

  # read stdout and stderr
  stdout, stderr = p.communicate()
  errors = stderr.decode('UTF-8')
  output = stdout.decode('UTF-8').splitlines()

  # clean up, if needed
  if fname:
    os.unlink(fname)

  # check for success
  if p.returncode != 0:
    msg = 'Profile failed with code %d.' % p.returncode
    print(msg)
    print(errors)
    sublime.set_timeout(lambda: sublime.status_message(msg), 0)
    return

  # parse result
  funcs = parse_output(output)
  hot_lines = [f.hot_lines(num_stddev=1) for f in funcs]
  hot_lines = [l for hl in hot_lines for l in hl]  # flatten hot lines
  results = '\n\n'.join(map(str, funcs))

  # display
  sublime.set_timeout(lambda: display_results(results, hot_lines), 0)


def display_results(results, hot_lines):
  scratch = sublime.active_window().new_file()
  scratch.set_scratch(True)
  scratch.set_name('Profile results')
  scratch.run_command('line_profiler_output',
                      {'profile_data': results, 'hot_lines': hot_lines})


def parse_output(lines):
  funcs = []
  curr_func = FunctionProfile()
  in_header = True
  code_col = 50  # guess
  for line in lines:
    if in_header:
      if line.startswith('File:'):
        curr_func.file_name = os.path.basename(line[6:])
      elif line.startswith('Function:'):
        curr_func.func_name = line.split()[1]
      elif line.startswith('Total time:'):
        curr_func.total_time = line[12:]
      elif line.startswith('Line #'):
        code_col = line.index('Line Contents')
      elif line.startswith('====='):
        in_header = False
    else:
      if len(line.strip()) == 0 or line.startswith('Timer unit'):
        in_header = True
        funcs.append(curr_func)
        curr_func = FunctionProfile()
        continue
      vals = line[:code_col].split()
      line_num = vals[0]
      hits, time, per_hit, percent = 0,0,0,0
      if len(vals) > 1:
        hits, time, per_hit, percent = vals[1:]
      curr_func.add_line(int(line_num), int(hits), int(time),
                         float(per_hit), float(percent), line.rstrip())
  return funcs


class FunctionProfile(object):
  """
  Represents output of the profiler for one function
  """
  def __init__(self):
    self.file_name = '<file>'
    self.func_name = '<func>'
    self.total_time = '<time>'
    self.lines = []
    self.sum_pct = 0
    self.sumsq_pct = 0

  def add_line(self, line_num, hits, time, per_hit, percent, line):
    # TODO: use the other stats somehow
    self.lines.append((percent, line))
    self.sum_pct += percent
    self.sumsq_pct += percent * percent

  def hot_lines(self, num_stddev=1):
    mean_pct = self.sum_pct / len(self.lines)
    var_pct = self.sumsq_pct / len(self.lines) - mean_pct**2
    thresh = mean_pct + num_stddev * math.sqrt(var_pct)
    if thresh > 0:
      print('threshold for', self.func_name, 'is', thresh, '% of total time')
      return [line for pct,line in self.lines if pct >= thresh]
    return []

  def __str__(self):
    if self.total_time == '0 s':
      return 'function %s in file %s was never run' % (self.func_name,
                                                       self.file_name)
    title = 'function %s in file %s took %s' % (
        self.func_name, self.file_name, self.total_time)
    lines = '\n'.join(line for _,line in self.lines)
    header = 'Line #      Hits         Time  Per Hit   % Time  Line Contents'
    return '\n'.join((title,'',header,'='*len(header),lines))
