#!/usr/bin/python
######################################################################
# Author : Aaron Benkoczy
# Date : 2021.01.26
######################################################################

import threading
import os
import re
import time
import sys
import tkinter
import time
import threading
import random
import queue
import tkinter as tk
from tkinter import font
from tkinter import messagebox
from fabric import Connection
import datetime

# HOST_NAME='balazs@abenkoczy.lionis.hu'
HOST_NAME='user@server'
#HOST_NAME='balazs@abenkoczy'
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'
SERVICE_REGEXP="foo"

class GuiPart:

  def Popup(self, title, text):
    win = tk.Toplevel()
    win.wm_title(title)
    l = tk.Label(win, text=text, font=("DejaVu", 8))
    l.grid(row=0, column=0)

    b= tk.Button(win, text="Okay", command=win.destroy)
    b.grid(row=1, column=0)

  def Mbox(self, title, text):
    return messagebox.showinfo(title=title, message=text, parent=self.master)

  status_labels = {}
  status_colors = {}

  # coloring status label
  def StatusColoring(self, status):
    statusColor = 'black'
    if(status == 'active'):
        statusColor = 'green'
    elif(status == 'failed'):
        statusColor = 'red'
    elif(status == 'sent'):    
        statusColor = 'grey'
    else:
        statusColor = 'grey'
    return statusColor

  def Killme():
    self.thr.kill()
    self.root.quit()
    self.root.destroy()

  def delete_last_lines(self, n=1):
    for _ in range(n):
      sys.stdout.write(CURSOR_UP_ONE)
      sys.stdout.write(ERASE_LINE)

  def on_frame_configure(self, event=None):
    self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all"))

  def task_width(self, event):
    canvas_width = event.width
    self.tasks_canvas.itemconfig(self.canvas_frame, width = canvas_width)

  def mouse_scroll(self, event):
    if event.delta:
      print('event.delta: ', event.delta)
      self.tasks_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    else:
      print('event.num: ', event.num)
      if event.num > 0:
          move = 1
      else:
          move = -1
      self.tasks_canvas.yview_scroll(move, "units")



    err = "#ERROR: No idea how to get those logs {}!".format(uname)
    raise Exit(err)

  def restartProcess(self, process):
    print ("process restart")
    global status_labels
    stdout = "sent"
    status_colors[process].config(fg = self.StatusColoring(stdout))
    status_labels[process].set(stdout)

    thr = threading.Thread(target=self.systemctlRestartProcess, args=(process,))
    thr.start() # Will run "foo"
    # thr.is_alive() # Will return whether foo is running currently
    # thr.join() # Will wait till "foo" is done

    # result = pool.apply_async(self.systemctlRestartProcess, process) # Evaluate "f(10)" asynchronously calling callback when finished.
    # stdout = self.systemctlRestartProcess(Connection('balazs@iekes'), process)

  def systemctlRestartProcess(self, process):
    print("connect to: " + str(process))
    c = Connection(HOST_NAME)
    uname = c.run('uname -s', hide=True)
    if 'Linux' in uname.stdout:
      #command = "df -h / | tail -n1 | awk '{print $5}'"
      command = "sudo systemctl restart " + process
      print(command)
      stdout=""
      stdout = c.run(command, hide=True).stdout.strip()
      print(stdout)
      return "sent"
        
    err = "Cannot execute command: {}!".format(uname)
    raise Exit(err)


  def logProcess(self, event, processName):
    print ("process log")
    # global status_labels
    # stdout = "sent"

    thr = threading.Thread(target=self.systemctlLog, args=(processName,))
    thr.start() # Will run "foo"
    # thr.is_alive() # Will return whether foo is running currently
    # thr.join() # Will wait till "foo" is done

    # result = pool.apply_async(self.systemctlRestartProcess, process) # Evaluate "f(10)" asynchronously calling callback when finished.
    # stdout = self.systemctlRestartProcess(Connection('balazs@iekes'), process)

  def statusUpdate(self, status_to_parse):
    global status_labels
    global status_colors
    SERVICE_UNIT_INDEX = 0
    SERVICE_LOAD_INDEX = 1
    SERVICE_ACTIVE_INDEX = 2
    SERVICE_SUB_INDEX = 3
    SERVICE_DESCRIPTION_INDEX = 4
    
    string_to_print = time.ctime() + " :: Status update\r"
    self.delete_last_lines()
    print(string_to_print)
    #print(string_to_print, end="\r") # python3

    # self.root.after(2000, self.statusUpdate)  # reschedule event in 2 seconds

    if re.search("\.service", status_to_parse):

      content = status_to_parse.strip()

      # iterate throu the splitted elements
      for i, line in enumerate(content.splitlines()):
        processName = ''
        processStatus = ''

        if re.search("\.service", line) and (re.search(SERVICE_REGEXP, line) or re.search("httpd", line)):
          line = " ".join(line.split())
          status_part = line.split(" ")
            
          if re.search("failed", line):
            processName = status_part[SERVICE_UNIT_INDEX+1].split('.')[0]
            processStatus = status_part[SERVICE_ACTIVE_INDEX+1]
              
          else:
            processName = status_part[SERVICE_UNIT_INDEX].split('.')[0]
            processStatus = status_part[SERVICE_ACTIVE_INDEX]

          # status_labels[processName].set(status_part[SERVICE_ACTIVE_INDEX+1])
          status_labels[processName].set(processStatus)
          status_colors[processName].config(fg = self.StatusColoring(processStatus))
    else:
      print('ERROR: Connection error.')

  def systemctlLog(self, process):
    print("connect to: " + str(process))
    c = Connection(HOST_NAME)
    uname = c.run('uname -s', hide=True)
    if 'Linux' in uname.stdout:
      #command = "df -h / | tail -n1 | awk '{print $5}'"
      # command = "sudo systemctl status httpd"
      # command = "sudo journalctl -u " + process + " | tail -n 5"
      command = self.processLogCommand(process)
      print(command)
      #command = "systemctl list-units --type=service --state=running"
      stdout = c.run(command, hide=True).stdout.strip()
      self.Popup("Log of " + process, stdout)
      print("--- log -------------------------")
      print(stdout)
      print("---------------------------------")
      print(">")
      return stdout

  def processLogCommand(self, process):
    command = "sudo journalctl -u " + process + " | tail -n 10"
    if(process == 'httpd'):
      command = 'sudo tail -n 10 /etc/httpd/logs/error_log'
    elif(process == 'failed'):
      command = 'red'
    elif(process == 'sent'):    
      command = 'grey'
    return command


  def createButtons(self, status_to_parse):
    global status_labels
    global status_colors
    status_labels = {}
    status_colors = {}
    SERVICE_UNIT_INDEX = 0
    SERVICE_LOAD_INDEX = 1
    SERVICE_ACTIVE_INDEX = 2
    SERVICE_SUB_INDEX = 3
    SERVICE_DESCRIPTION_INDEX = 4

    if re.search("\.service", status_to_parse):

      content = status_to_parse.strip()

      # iterate throu the splitted elements
      for i, line in enumerate(content.splitlines()):
        processName = ''
        processStatus = ''

        if re.search("\.service", line) and (re.search(SERVICE_REGEXP, line) or re.search("httpd", line)):
          line = " ".join(line.split())
          status_part = line.split(" ")

          if re.search("failed", line):
            processName = status_part[SERVICE_UNIT_INDEX+1].split('.')[0]
            processStatus = status_part[SERVICE_ACTIVE_INDEX+1]
          else:
            processName = status_part[SERVICE_UNIT_INDEX].split('.')[0]
            processStatus = status_part[SERVICE_ACTIVE_INDEX]

          onclickButton = lambda d=processName: self.restartProcess(d)
          
          button_button = tk.Button(self.tasks_frame, height = 1, command = onclickButton, width = 20,
              text = processName)
          button_button.grid(row = i, column = 1)
          status_labels[processName] = tk.StringVar(self.tasks_frame)
          button_label = tk.Label(self.tasks_frame, height = 1, text=processStatus, textvariable = status_labels[processName])
          button_label.grid(row = i, column = 2)

          ## click on label
          onclickLabel = lambda event, arg=processName: self.logProcess(event, arg)
          button_label.bind("<ButtonPress-1>", onclickLabel)
          status_colors[processName] = button_label

          status_labels[processName].set(processStatus)
          status_colors[processName].config(fg = self.StatusColoring(processStatus))

  def systemctlStatus(self, c):
    uname = c.run('uname -s', hide=True)
    if 'Linux' in uname.stdout:
      #command = "df -h / | tail -n1 | awk '{print $5}'"
      # command = "sudo systemctl status httpd"
      command = "systemctl list-units --type=service"
      #command = "systemctl list-units --type=service --state=running"
      stdout = c.run(command, hide=True).stdout.strip()
      return stdout

    err = "#ERROR: No idea how to get the status {}!".format(uname)
    raise Exit(err)

  def __init__(self, master, queue, endCommand):
    self.queue = queue
    self.master = master
    # Set up the GUI    
    self.master.protocol("WM_DELETE_WINDOW", endCommand)    
    self.master.title("SSH Status")
    # master.root.geometry('10x10+0+0')
    self.master.dFont=font.Font(family="Arial", size=14) # python 3
    self.master.geometry('300x900+0+0')
    # Menu elements
    # master.menu = Menu(master.root)
    # master.root.config(menu=master.menu)
    # master.fileMenu = Menu(master.menu)
    # master.menu.add_cascade(label="File", menu=master.fileMenu)
    # master.fileMenu.add_command(label="Refresh", command=master.RefreshMenu)

    self.tasks_canvas = tk.Canvas(self.master)

    self.tasks_frame = tk.Frame(self.tasks_canvas)
    self.text_frame = tk.Frame(self.tasks_canvas)


    self.canvas_frame = self.tasks_canvas.create_window((0, 0), window=self.tasks_frame, anchor="n")

    print(">>>> Start <<<<")
    print("connect to: " + HOST_NAME)
    print(">")


    CONNECTION = Connection(HOST_NAME)
    status_to_parse = self.systemctlStatus(CONNECTION)
    self.createButtons(status_to_parse);

    self.scrollbar = tk.Scrollbar(self.tasks_canvas, orient="vertical", command=self.tasks_canvas.yview)

    self.tasks_canvas.configure(yscrollcommand=self.scrollbar.set)

    self.tasks_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

 
    self.tasks_frame.pack(side=tk.BOTTOM, fill=tk.X)
    self.text_frame.pack(side=tk.BOTTOM, fill=tk.X)

    #scroll bar to root
    # self.yscrollbar=Scrollbar(self.frame, orient=VERTICAL, command=self.root.yview)
    # self.yscrollbar.pack(side=RIGHT, fill=Y)

    # self.xscrollbar=Scrollbar(self.frame, orient=HORIZONTAL, command=self.root.xview)
    # self.xscrollbar.pack(side=BOTTOM, fill=X)

    # self.root.configure(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)
    # self.canvas.configure(scrollregion=self.canvas.bbox("all"),width=200,height=200)
    
    # self.frame.pack(anchor=W, fill=Y, expand=True)
    

    # self.root.bind("<Return>", self.createButtons)
    # self.bind("<Configure>", self.on_frame_configure)
    # self.bind_all("<MouseWheel>", self.mouse_scroll)
    # self.bind_all("<Button-4>", self.mouse_scroll)
    # self.bind_all("<Button-5>", self.mouse_scroll)
    self.tasks_canvas.bind("<Configure>", self.task_width)

    # self.root.after(2000, self.statusUpdate);
    # thr = threading.Thread(target=self.statusUpdate)
    # self.thr = threading.Thread(target=self.loop)
    # self.thr.start() # Will run "foo"

    # self.root.mainloop();

  def processIncoming(self):
    """Handle all messages currently in the queue, if any."""
    print(datetime.datetime.now())
    while self.queue.qsize(  ):
      try:
        services = self.queue.get(0)
        self.statusUpdate(services)
      except queue.Empty:
        pass

    logFile = ""

  # double click on a node
  def OnDoubleClick(self, event):
    selected_item = self._tree.focus()
    value = self._tree.item(selected_item, "values")
    if (len(value) > 0):
      print ("===============================================================")
      print (value)
      if re.search("http", value[0]):
        url = value[0]
        print(url)
        webbrowser.open_new(url)
    print ("===============================================================")

  def RefreshTree(self,content):
    self._tree.delete(*self._tree.get_children())
    self.GetData(content)

  def GetData(self, content):
    contentList = content.split("\n")
    tagMap = {}
    tagIndex = 0

    # iterate throu the splitted elements
    for i, line in enumerate(contentList):
      
      if (re.search("href=", line)):
        issue_text = line[0:line.find("|")]
        link = line[line.find("=")+1:len(line)]
        tagMap[tagIndex] = self._tree.insert("", tagIndex, i, text=issue_text,
          values=(link, "placeColumn"));

      else:
        issue_text = line
        link = "--"
        tagMap[tagIndex] = self._tree.insert("", tagIndex, i, text=issue_text,
          values=(link, "placeColumn"));

      tagIndex = tagIndex + 1



class ThreadedClient:


  def systemctlStatus(self, c):
    uname = c.run('uname -s', hide=True)
    if 'Linux' in uname.stdout:
      #command = "df -h / | tail -n1 | awk '{print $5}'"
      # command = "sudo systemctl status httpd"
      command = "systemctl list-units --type=service"
      #command = "systemctl list-units --type=service --state=running"
      stdout = c.run(command, hide=True).stdout.strip()
      return stdout

    err = "#ERROR: No idea how to get the status {}!".format(uname)
    raise Exit(err)


  def __init__(self, master):
    self.master = master

    ## call periodically
    # Create the queue
    self.queue = queue.Queue(  )

    # Set up the GUI part
    self.gui = GuiPart(master, self.queue, self.endApplication)

    # Set up the thread to do asynchronous I/O
    # More threads can also be created and used, if necessary
    self.running = 1
    self.thread1 = threading.Thread(target=self.workerThread1)
    self.thread1.start(  )

    # Start the periodic call in the GUI to check if the queue contains
    # anything
    self.periodicCall(  )

  def periodicCall(self):
    self.gui.processIncoming(  )
    if not self.running:
      import sys
      sys.exit(1)
      self.thread1.exit()

    self.master.after(10000, self.periodicCall)

  def workerThread1(self):
    CONNECTION = Connection(HOST_NAME)
    while self.running:
      if(CONNECTION):
        status_to_parse = self.systemctlStatus(CONNECTION)
        self.queue.put(status_to_parse)

  def endApplication(self):
    self.running = 0
    import sys
    sys.exit(1)

root = tk.Tk()
# master=tk.Tk()
client = ThreadedClient(root)
root.mainloop(  )
