from __future__ import print_function
import math
import os.path


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
    print('threshold is', thresh, '% of total time')
    return [line for pct,line in self.lines if pct >= thresh]

  def __str__(self):
    lines = '\n'.join(line for _,line in self.lines)
    title = 'function %s in file %s took %s' % (
        self.func_name, self.file_name, self.total_time)
    header = 'Line #      Hits         Time  Per Hit   % Time  Line Contents'
    return '\n'.join((title,'',header,'='*len(header),lines))
