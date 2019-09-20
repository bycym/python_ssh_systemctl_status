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
# import sys
from Tkinter import *
import tkFont
import ttk
from fabric import Connection

HOST_NAME='user@hostname'

class App:

    status_labels = {}
    status_colors = {}

    # coloring status label
    def StatusColoring(self, status):
        statusColor = 'grey'
        if(status == 'active'):
            statusColor = 'green'
        elif(status == 'failed'):
            statusColor = 'red'
        elif(status == 'sent'):    
            statusColor = 'yellow'
        else:
            statusColor = 'grey'
        return statusColor

    def Killme():
        self.root.quit()
        self.root.destroy()

    def RefreshMenu(self):
        print("refresh")

    def restartProcess(self, process):
        print ("process restart")
        global status_labels
        stdout = "sent"
        
        thr = threading.Thread(target=self.systemctlRestartProcess, args=(process,))
        thr.start() # Will run "foo"
        # thr.is_alive() # Will return whether foo is running currently
        # thr.join() # Will wait till "foo" is done

        # result = pool.apply_async(self.systemctlRestartProcess, process) # Evaluate "f(10)" asynchronously calling callback when finished.
        # stdout = self.systemctlRestartProcess(Connection('balazs@iekes'), process)

        status_labels[process].set(stdout)


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
            command = "sudo systemctl status httpd"
            command = "systemctl list-units --type=service"
            #command = "systemctl list-units --type=service --state=running"
            stdout = c.run(command, hide=True).stdout.strip()
            return stdout

        err = "#ERROR: No idea how to get disk space on {}!".format(uname)
        raise Exit(err)


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

        processName = ''
        processStatus = ''

        if re.search("\.service", status_to_parse):

            content = status_to_parse.strip()

            # contentList = content.splitlines()


            # iterate throu the splitted elements
            for i, line in enumerate(content.splitlines()):

                if re.search("\.service", line):
                    #tag = "["+line[line.find("[")+1:line.find("]")]+"]"
                    line = " ".join(line.split())
                    status_part = line.split(" ")

                    if re.search("failed", line):
                        processName = status_part[SERVICE_UNIT_INDEX+1].split('.')[0]
                        processStatus = status_part[SERVICE_ACTIVE_INDEX+1]
                        # print(status_part[SERVICE_UNIT_INDEX+1],' :: ', status_part[SERVICE_ACTIVE_INDEX+1])
                    else:
                        processName = status_part[SERVICE_UNIT_INDEX].split('.')[0]
                        processStatus = status_part[SERVICE_ACTIVE_INDEX]

                    onclick = lambda d=processName: self.restartProcess(d)
                    button_button = Button(self.root, height = 1, command = onclick, width = 20,
                        text = processName)
                    button_button.grid(row = i, column = 1)
                    status_labels[processName] = StringVar(self.root)
                    button_label = Label(self.root, height = 1, text=processStatus, textvariable = status_labels[processName])
                    button_label.grid(row = i, column = 2)
                    status_colors[processName] = button_label


    def statusUpdate(self):
        global status_labels
        global status_colors
        SERVICE_UNIT_INDEX = 0
        SERVICE_LOAD_INDEX = 1
        SERVICE_ACTIVE_INDEX = 2
        SERVICE_SUB_INDEX = 3
        SERVICE_DESCRIPTION_INDEX = 4
        CONNECTION = Connection(HOST_NAME)

        status_to_parse = self.systemctlStatus(CONNECTION)
        processName = ""
        processStatus = ""
        statusColor = ""

        print("Status update")
        self.root.after(2000, self.statusUpdate)  # reschedule event in 2 seconds

        if re.search("\.service", status_to_parse):

            content = status_to_parse.strip()

            # iterate throu the splitted elements
            for i, line in enumerate(content.splitlines()):

                if re.search("\.service", line):
                    line = " ".join(line.split())
                    status_part = line.split(" ")
                    
                    if re.search("failed", line):
                        processName = status_part[SERVICE_UNIT_INDEX+1].split('.')[0]
                        status_labels[processName].set(status_part[SERVICE_ACTIVE_INDEX+1])
                    else:
                        processName = status_part[SERVICE_UNIT_INDEX].split('.')[0]
                        status_labels[processName].set(status_part[SERVICE_ACTIVE_INDEX])

                    status_labels[processName].set(processStatus)
                    status_colors[processName].config(fg = self.StatusColoring(processStatus))


    def __init__(self):

        self.root=Tk()
        self.root.title("SSH Status")
        self.root.geometry('10x10+0+0')
        self.dFont=tkFont.Font(family="Arial", size=14)

        # Menu elements
        self.menu = Menu(self.root)
        self.root.config(menu=self.menu)
        self.fileMenu = Menu(self.menu)
        self.menu.add_cascade(label="File", menu=self.fileMenu)
        self.fileMenu.add_command(label="Refresh", command=self.RefreshMenu)


        self.createButtons();

        #scroll bar to root
        # self.yscrollbar=Scrollbar(self.root, orient=VERTICAL, command=self.root.yview)
        # self.yscrollbar.pack(side=RIGHT, fill=Y)

        # self.xscrollbar=Scrollbar(self.root, orient=HORIZONTAL, command=self.root.xview)
        # self.xscrollbar.pack(side=BOTTOM, fill=X)

        # self.root.configure(yscrollcommand=self.yscrollbar.set, xscrollcommand=self.xscrollbar.set)

        self.root.geometry('600x600+0+0')

        self.root.after(2000, self.statusUpdate);
        self.root.mainloop();


if __name__ == '__main__':
    app = App()
