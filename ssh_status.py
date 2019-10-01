#!/usr/bin/python
######################################################################
# Author : Aaron Benkoczy
# Date : 2019.09.16
######################################################################
# https://stackoverflow.com/questions/25976959/python-creating-dynamic-button
# onclick = lambda url=url[1]: urlOpen(url)
# https://www.delftstack.com/howto/python-tkinter/how-to-pass-arguments-to-tkinter-button-command/
# https://stackoverflow.com/questions/25976959/python-creating-dynamic-button
# https://stackoverflow.com/questions/19837486/python-lambda-in-a-loop
# https://stackoverflow.com/questions/24849265/how-do-i-create-an-automatically-updating-gui-using-tkinter
# https://stackoverflow.com/questions/24282331/getting-values-of-dynamically-generated-entry-fields-using-tkinter
# https://stackoverflow.com/questions/1239035/asynchronous-method-call-in-python


import threading
import os
import re
import time
import sys

### python 3
#from tkinter import *
#from tkinter import font
## end python 3

### python 2
import tkFont
from Tkinter import *
## end python 2




from fabric import Connection

HOST_NAME='user@server'
CURSOR_UP_ONE = '\x1b[1A'
ERASE_LINE = '\x1b[2K'

class App:

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

    # def RefreshMenu(self):
    #     print("refresh")

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


    def processLogCommand(self, process):
        command = "sudo journalctl -u " + process + " | tail -n 10"
        if(process == 'httpd'):
            command = 'sudo tail -n 10 /etc/httpd/logs/error_log'
        elif(process == 'failed'):
            command = 'red'
        elif(process == 'sent'):    
            command = 'grey'
        return command


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
            print("--- log -------------------------")
            print(stdout)
            print("---------------------------------")
            print(">")
            return stdout

        err = "#ERROR: No idea how to get those logs {}!".format(uname)
        raise Exit(err)

    def statusUpdate(self):
        global status_labels
        global status_colors
        SERVICE_UNIT_INDEX = 0
        SERVICE_LOAD_INDEX = 1
        SERVICE_ACTIVE_INDEX = 2
        SERVICE_SUB_INDEX = 3
        SERVICE_DESCRIPTION_INDEX = 4

        CONNECTION = Connection(HOST_NAME)

        if(CONNECTION):

            status_to_parse = self.systemctlStatus(CONNECTION)
            
            string_to_print = time.ctime() + " :: Status update\r"
            self.delete_last_lines()
            print(string_to_print)
            #print(string_to_print, end="\r") # python3

            self.root.after(2000, self.statusUpdate)  # reschedule event in 2 seconds

            if re.search("\.service", status_to_parse):

                content = status_to_parse.strip()

                # iterate throu the splitted elements
                for i, line in enumerate(content.splitlines()):
                    processName = ''
                    processStatus = ''

                    if re.search("\.service", line):
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


    def createButtons(self):
        global status_labels
        global status_colors
        status_labels = {}
        status_colors = {}
        SERVICE_UNIT_INDEX = 0
        SERVICE_LOAD_INDEX = 1
        SERVICE_ACTIVE_INDEX = 2
        SERVICE_SUB_INDEX = 3
        SERVICE_DESCRIPTION_INDEX = 4

        CONNECTION = Connection(HOST_NAME)

        status_to_parse = self.systemctlStatus(CONNECTION)

        if re.search("\.service", status_to_parse):

            content = status_to_parse.strip()

            # iterate throu the splitted elements
            for i, line in enumerate(content.splitlines()):
                processName = ''
                processStatus = ''
                if re.search("\.service", line):
                    line = " ".join(line.split())
                    status_part = line.split(" ")

                    if re.search("failed", line):
                        processName = status_part[SERVICE_UNIT_INDEX+1].split('.')[0]
                        processStatus = status_part[SERVICE_ACTIVE_INDEX+1]
                    else:
                        processName = status_part[SERVICE_UNIT_INDEX].split('.')[0]
                        processStatus = status_part[SERVICE_ACTIVE_INDEX]

                    onclickButton = lambda d=processName: self.restartProcess(d)
                    
                    button_button = Button(self.tasks_frame, height = 1, command = onclickButton, width = 20,
                        text = processName)
                    button_button.grid(row = i, column = 1)
                    status_labels[processName] = StringVar(self.tasks_frame)
                    button_label = Label(self.tasks_frame, height = 1, text=processStatus, textvariable = status_labels[processName])
                    button_label.grid(row = i, column = 2)

                    ## click on label
                    onclickLabel = lambda event, arg=processName: self.logProcess(event, arg)
                    button_label.bind("<ButtonPress-1>", onclickLabel)
                    status_colors[processName] = button_label

                    status_labels[processName].set(processStatus)
                    status_colors[processName].config(fg = self.StatusColoring(processStatus))

    def loop(self):
        while True:
            self.statusUpdate()
            time.sleep(120) # Delay for 1 minute (60 seconds).
        # thr = threading.Thread(target=self.statusUpdate)
        # thr.start() # Will run "foo"


    def __init__(self):

        self.root=Tk()
        self.root.title("SSH Status")
        # self.root.geometry('10x10+0+0')
        #self.dFont=font.Font(family="Arial", size=14) # python 3
        self.dFont=tkFont.Font(family="Arial", size=14)

        # Menu elements
        # self.menu = Menu(self.root)
        # self.root.config(menu=self.menu)
        # self.fileMenu = Menu(self.menu)
        # self.menu.add_cascade(label="File", menu=self.fileMenu)
        # self.fileMenu.add_command(label="Refresh", command=self.RefreshMenu)

        self.tasks_canvas = Canvas(self.root)

        self.tasks_frame = Frame(self.tasks_canvas)
        self.text_frame = Frame(self.root)

        self.scrollbar = Scrollbar(self.tasks_canvas, orient="vertical", command=self.tasks_canvas.yview)

        self.tasks_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.tasks_canvas.pack(side=TOP, fill=BOTH, expand=1)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.canvas_frame = self.tasks_canvas.create_window((0, 0), window=self.tasks_frame, anchor="n")

        print(">>>> Start <<<<")
        print("connect to: " + HOST_NAME)
        print(">")
        self.createButtons();

        self.text_frame.pack(side=BOTTOM, fill=X)

        #scroll bar to root
        # self.yscrollbar=Scrollbar(self.frame, orient=VERTICAL, command=self.root.yview)
        # self.yscrollbar.pack(side=RIGHT, fill=Y)

        # self.xscrollbar=Scrollbar(self.frame, orient=HORIZONTAL, command=self.root.xview)
        # self.xscrollbar.pack(side=BOTTOM, fill=X)

        # self.root.configure(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)
        # self.canvas.configure(scrollregion=self.canvas.bbox("all"),width=200,height=200)
        self.root.geometry('300x600+0+0')
        # self.frame.pack(anchor=W, fill=Y, expand=True)
        

        # self.root.bind("<Return>", self.createButtons)
        self.root.bind("<Configure>", self.on_frame_configure)
        self.root.bind_all("<MouseWheel>", self.mouse_scroll)
        self.root.bind_all("<Button-4>", self.mouse_scroll)
        self.root.bind_all("<Button-5>", self.mouse_scroll)
        self.tasks_canvas.bind("<Configure>", self.task_width)

        self.root.after(2000, self.statusUpdate);
        # thr = threading.Thread(target=self.statusUpdate)
        # self.thr = threading.Thread(target=self.loop)
        # self.thr.start() # Will run "foo"

        self.root.mainloop();
        
        

if __name__ == '__main__':
    app = App()
