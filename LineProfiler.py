import os
import sublime
import sublime_plugin
import subprocess
import tempfile
import time
import threading

# Load settings on plugin load
s = sublime.load_settings('LineProfiler.sublime-settings')
PYTHON = s.get('python')
KERNPROF = s.get('kernprof')
PYTHONPATH = s.get('pythonpath')
POLL_SLEEP_SECONDS = s.get('poll_sleep_seconds')
POLL_TIMEOUT_SECONDS = s.get('poll_timeout_seconds')


class LineProfilerCommand(sublime_plugin.TextCommand):
  def is_enabled(self):
    return 'source.python' in self.view.scope_name(0)

  def run(self, edit):
    if not self.is_enabled():
      return

    # set up paths
    fname = self.view.file_name()
    is_tmpfile = False
    env = os.environ.copy()
    if fname is None:
      env['PYTHONPATH'] = PYTHONPATH
    else:
      env['PYTHONPATH'] = os.path.dirname(fname) + os.pathsep + PYTHONPATH

    # write the file if it's not saved right now
    if fname is None or self.view.is_dirty():
      contents = self.view.substr(sublime.Region(0, self.view.size()))
      with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as fh:
        fh.write(bytes(contents, 'UTF-8'))
        fname = fh.name
      is_tmpfile = True

    # run kernprof with the correct paths
    p = subprocess.Popen([PYTHON, KERNPROF,'-lbv','-o','/dev/null',fname], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

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
  # poll for results
  tic = time.time()
  while p.poll() is None:
    if time.time() - tic > POLL_TIMEOUT_SECONDS:
      print('kernprof timed out, killing process')
      p.kill()
      return
    time.sleep(POLL_SLEEP_SECONDS)

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

  # parse result
  file_name, func_name, profile = '<file>', '<func>', ''
  for i,line in enumerate(output):
    if line.startswith('File:'):
      file_name = os.path.basename(line[6:])
    elif line.startswith('Function:'):
      func_name = line.split()[1]
    elif line.startswith('====='):
      profile = '\n'.join(x.rstrip() for x in output[i-3:])  # include header and total time
      break

  # display
  scratch = window.new_file()
  scratch.set_scratch(True)
  scratch.set_name('Profile of %s::%s' % (file_name, func_name))
  scratch.run_command('line_profiler_output', {'profile_data': profile})
