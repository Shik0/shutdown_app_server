# -*- coding: utf-8 -*-
#############################################################
# author Shahin Mikayilov (mikailovsh@gmail.com)            #
#                                                           #
# 27.08.2018                                                #
# Please, add a comment if you make any changes on this file#
#############################################################
import os
import serial
import time
import sys
import pickle
import base64
import paramiko


# shutdown the sapides server
def shutdown_sapides(hostKey, uname, passwd, ipaddr, command):
    """
    Function sends shutdown command to the sapides server to shutdown it.
    Paramiko tool is used to connect securely to the server. Host key has
    been taken from sapides server, if this key does not exist then
    unsecure connection is used. paramiko's connect method accept three
    parameters.
    command variable type is list and contains two commands.
    As a result function returns boolean value: True or False.
    True - sapides has been successfully shuted down
    False - exception raised
    """
    key = paramiko.RSAKey(data=base64.b64decode(hostKey))
    client = paramiko.SSHClient()
    client.get_host_keys().add(ipaddr, 'ssh-rsa', key)
    try:
        client.connect(ipaddr, username=uname, password=passwd)
        client.exec_command(command[0])
        client.exec_command(command[1])
        result = True
    except:
        result = False
    client.close()
    return result


# shutdown the saprouter server
def shutdown_saprouter(hostKey, uname, passwd, ipaddr, command):
    """
    Function sends shutdown command to the saprouter server to shutdown it.
    Paramiko tool is used to connect securely to the server. Host key has
    been taken from saprouter server, if this key does not exist then
    unsecure connection is used. paramiko's connect method accept three
    parameters.
    As a result function returns boolean value: True or False.
    True - saprouter has been successfully shuted down
    False - exception raised
    """
    key = paramiko.RSAKey(data=base64.b64decode(hostKey))
    client = paramiko.SSHClient()
    client.get_host_keys().add(ipaddr, 'ssh-rsa', key)
    try:
        client.connect(ipaddr, username=uname, password=passwd)
        client.exec_command(command)
        result = True
    except:
        result = False
    client.close()
    return result


# shutdown the ESXi server
def shutdown_esx(hostKey, uname, passwd, ipaddr, command):
    """
    Function sends shutdown command to the ESXi server to shutdown it.
    Paramiko tool is used to connect securely to the server. Host key has
    been taken from the ESXi server, if this key does not exist then
    unsecure connection is used. paramiko's connect method accept three
    parameters.
    As a result function returns boolean value: True or False.
    True - ESXi has been successfully shuted down
    False - exception raised
    """
    key = paramiko.RSAKey(data=base64.b64decode(hostKey))
    client = paramiko.SSHClient()
    client.get_host_keys().add(ipaddr, 'ssh-rsa', key)
    try:
        client.connect(ipaddr, username=uname, password=passwd)
        client.exec_command(command)
        result = True
    except:
        result = False
    client.close()
    return result


def startCheck():
    """
    sys.stdout command used to redirect all terminal outputs to the
    log file. There are two log files here: USBConnection.txt and
    pythonLog.txt, and each log file contains related information.
    Path for log files is /tmp/pythonSAP/
    Using python serial package we try to connect to the USB device. Here using
    while loop we do it 4 times. Script writes connection result to the log.
    USB device sends 2 signals: 0 - no electricity, 1 - has electricity
    Script compares last 3 runs results. If there is minimum one "1" signal,
    then it means that electricity came back after a while (for example 2
    minutes and no any server will be shuted down). Otherwise, scipt will run
    shutdown procedures.
    Pickle is a built-in python package and it was used here to loading and
    dumping of session results (easy and simple way).
    """
	sapides_ip = '192.168.0.104'
	saprouter_ip = '192.168.0.106'
	esxi_ip = '192.168.0.220'
    with open("/tmp/pythonSAP/USBConnection.txt", "a") as f:
        # redirect all terminal outputs to the file
        sys.stdout = f
        # connect to the USB device
        n = 4  # try to connect to the usb evice 4 times
        while n >= 0:
            if n == 0:
                sys.exit()
            try:
                usbDevice = serial.Serial("/dev/ttyUSB0", 9600)
                t = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.localtime())
                print(t, "Connected to the USB")
                break
            except:
                usbDevice = False
                t = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.localtime())
                message = "Could not connect to the USB device."
                print(t, message)
            # if first connection attempt failed, then try again after 3 sec
            time.sleep(3)
            n-=1
        # read serial data ( 1 - has electricity, 0 - power off )
        # check usb signal five times
        checkPower = []
        for i in range(5):
            if "1" in str(usbDevice.readline()):
                checkPower.append(1)
            time.sleep(1)
        # script checks 3 previous status of the usb signal,
        # if all of those were 0 then shutdown the server
        # create file for the previous session, if it does not exist
        try:
            prevSignal = pickle.load(open('/tmp/pythonSAP/session.p', 'rb'))
            # store only one week data
            if len(prevSignal) >= 10083:   # 60*24*7 + 3
                prevSignal = prevSignal[:3].copy()
        except:
            message = "session file does not exists. will be created"
            print(message)
            prevSignal = []
            pickle.dump(prevSignal, open('/tmp/pythonSAP/session.p', 'wb'))
            prevSignal = pickle.load(open('/tmp/pythonSAP/session.p', 'rb'))
        # if result of for loop was positive then add 1 (has an electricity)
        # to the list
        if len(checkPower) > 0:
            prevSignal.append(1)
        else:
            prevSignal.append(0)
        # update the session.p file with current session value
        pickle.dump(prevSignal, open('/tmp/pythonSAP/session.p', 'wb'))
        # check last 3 session result, if length less than 3 then
        # dont do anything
        if len(prevSignal) >= 3:
            results = prevSignal[-1:-4:-1]  # get last 3 sessions
            if 1 in results:
                shutdown = False  # do not do anything
            else:
                # if the result of last three sessions was 0 then
                # shutdown the system
                shutdown = True  # server will be shutted down
        else:
            shutdown = False  # do not do anything
        if shutdown:
            # no electricity, shutting down the SAPIdes
            os.system("date >> /tmp/pythonSAP/pythonLog.txt")
            os.system("echo shutdown the SAP")
            hostKey = open("/home/ubuntuser/SAPIdes.txt", "rb").read()
            uname, passwd = 'idsadm', $SIDADM_PASS # set this env variable beforehand
            ipaddr, command = sapides_ip, [
                    'stopsap sapides >> /tmp/pythonSAP/pythonLog.txt',
                    'shutdown now'
                    ]
            shutdownSAPIDES = shutdown_sapides(
                    hostKey, uname, passwd, ipaddr, command
                    )
            # write sapides shutdown result to the log
            if shutdownSAPIDES:
                t = time.strftime(
                        "%a, %d %b %Y %H:%M:%S +0000",
                        time.localtime()
                        )
                print(t, " sapides shutdown completed")
            else:
                t = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.localtime()
                                  )
                print(t, "Could not shutdown saprouter")         
            """
            Use this command if you shut down the sap system through itself
            os.system(
                    "su - idsadm -c 'stopsap sapides >> /tmp/pythonSAP/pythonLog.txt'"
                    )
            """
            # shutdown saprouter
            hostKey = open("/home/ubuntuser/SAPRouter.txt", "rb").read()
            uname, passwd = 'root', $SAPROUTER_PASS
            ipaddr, command = saprouter_ip, 'shutdown now'
            shutdownSaprouter = shutdown_saprouter(
                    hostKey, uname, passwd, ipaddr, command
                    )
            # write saprouter shutdown result to the log
            if shutdownSaprouter:
                t = time.strftime(
                        "%a, %d %b %Y %H:%M:%S +0000",
                        time.localtime()
                        )
                print(t, " saprouter shutdown completed")
            else:
                t = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.localtime()
                                  )
                print(t, "Could not shutdown saprouter")
            # shutdown esxi
            hostKey = open("/home/ubuntuser/ESXi.txt", "rb").read()
            uname, passwd = 'root', $ESXIROOT_PASS
            ipaddr, command = esxi_ip, 'halt'
            shutdownESX = shutdown_esx(hostKey, uname, passwd, ipaddr, command)
            # write esx shutdown result to the log
            if shutdownESX:
                t = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.localtime()
                                  )
                print(t, " esx shutdown completed")
            else:
                t = time.strftime("%a, %d %b %Y %H:%M:%S +0000",
                                  time.localtime()
                                  )
                print(t, "Could not shutdown esx")
        else:
            t = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime())
            print(t, checkPower, "-->current session")
            os.system("date >> /tmp/pythonSAP/pythonLog.txt")
            os.system("echo connection is OK >> /tmp/pythonSAP/pythonLog.txt")


if __name__ == "__main__":
    startCheck()
