import os
import sublime
import sublime_plugin
import subprocess
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


if (sys.version_info[0] == 2):
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
        env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # set up the output catcher thread
    window = self.view.window()
    if not is_tmpfile:
      fname = None
    threading.Thread(target=read_output, args=(window, p, fname)).start()


class LineProfilerOutputCommand(sublime_plugin.TextCommand):
  def run(self, edit, profile_data=None):
    if profile_data is None:
      print('This command should only be called by line_profiler')
      return
    self.view.insert(edit,0, profile_data)
    self.view.set_read_only(True)


def read_output(window, p, fname):
  poll_timeout = SETTINGS.get('poll_timeout_seconds', 60)
  poll_sleep = SETTINGS.get('poll_sleep_seconds', 1)
  # poll for results
  tic = time.time()
  while p.poll() is None:
    if time.time() - tic > poll_timeout:
      print('kernprof timed out, killing process')
      p.kill()
      return
    time.sleep(poll_sleep)

  # read stdout and stderr
  stdout, stderr = p.communicate()
  errors = stderr.decode('UTF-8')
  output = stdout.decode('UTF-8').splitlines()

  # clean up, if needed
  if fname:
    os.unlink(fname)

  # check for success
  if p.returncode != 0:
    print('kernprof exited with code %d' % p.returncode)
    print(errors)
    return

  # parse result (TODO: handle multiple profiled functions)
  file_name, func_name, profile = '<file>', '<func>', ''
  for i,line in enumerate(output):
    if line.startswith('File:'):
      file_name = os.path.basename(line[6:])
    elif line.startswith('Function:'):
      func_name = line.split()[1]
    elif line.startswith('====='):
      # include header and total time
      profile = '\n'.join(x.rstrip() for x in output[i-3:])
      break

  # display
  sublime.set_timeout(lambda: display_results(file_name, func_name, profile), 0)

def display_results(file_name, func_name, profile):
  scratch = sublime.active_window().new_file()
  scratch.set_scratch(True)
  scratch.set_name('Profile of %s::%s' % (file_name, func_name))
  scratch.run_command('line_profiler_output', {'profile_data': profile})
