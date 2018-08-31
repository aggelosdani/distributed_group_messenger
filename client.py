import zmq
import sys
import socket
import select
import ast
import threading
import time

flag=1
startlatency=0
endlatency=0
number_of_messages=0

if (len(sys.argv) < 4):
    print "Usage: python client.py [port] [username] [ip] [message_file](optional)"
    sys.exit()

groups_members = {}
current_group = None
mycounters={}
cost=0

host = sys.argv[3]
port = int(sys.argv[1])
username = sys.argv[2]

my_id = 0
context = zmq.Context()

#keep alive messages
def keepalive():
    global cost
    while True:
        keepalive_context = zmq.Context()
        heartbeat_sock = keepalive_context.socket(zmq.REQ)
        heartbeat_sock.connect("tcp://" + 'localhost'  + ":5555")
        cost+=1
        heartbeat_sock.send("!heartbeat "+my_id)
        time.sleep(5)

# client give commands from stdin
def messages(line):
    global current_group
    global cost

    user_input = line.rstrip("\n ")
    user_input = ' '.join(user_input.split())

    if user_input.startswith('!w'):
        command = user_input.split(' ')
        args_size = len(command) - 1

        if (args_size != 1):
            print "Please give me a group name"

        elif (not groups_members.has_key(command[1])):
            print "Please join or create the group in order to send a message!"
        else:
            current_group = command[1]


    elif (user_input.startswith('!')):
        cost+=1
        tcp_sock.send(user_input + " " + my_id)
        message = tcp_sock.recv()
        if (user_input=="!q"):
            sys.exit()
        if (message.startswith('*')):
            print "Error: ", message.lstrip('*')
        else:
            if user_input.startswith('!j'):
                command = user_input.split(' ')
                groups_members[command[1]] = list(ast.literal_eval(message))
                mycounters[command[1]]={}
                for item in groups_members[command[1]][::-1]:
                    mycounters[command[1]][item[3]]=0
                print "Reply from server: [ %s ]" % message
            else:
                print "Reply from server: [ %s ]" % message
    else:
        if (current_group is None):
            print "Please select a group in order to send a message!!!"
        else:
            cost+=1
            tcp_sock.send("!u "+current_group)
            current_members=tcp_sock.recv()
            groups_members[current_group]=list(ast.literal_eval(current_members))
            for item in groups_members[current_group][::-1]:
                if (not item[3] in mycounters[current_group]):
                    mycounters[current_group][item[3]]=0
            mycounters[current_group][username]+=1
            counter=mycounters[current_group][username]

            startlatency=time.time()
            for item in groups_members[current_group][::-1]:
                cost+=1
                udp_sock.sendto(str(counter)+"~"+str(startlatency)+"~"+"in " + current_group + ' ' + username + " says: " + user_input, (item[1], int(item[2])))

    sys.stdout.write("[%s]>" %username);sys.stdout.flush()



#Connect to server
tcp_sock = context.socket(zmq.REQ)
tcp_sock.connect("tcp://" + 'localhost'  + ":5555")

#register
cost+=1
tcp_sock.send(b"!r %s %s %s" %(host, port, username))
message = tcp_sock.recv()
if (message.startswith('*')):
    print ("Error: ", message.lstrip('*'))
else:
    my_id = message
    print ("ID: %s" %my_id)

sys.stdout.write("[%s]>" %username)
sys.stdout.flush()

# udp sockets.
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Make Socket Reusable
udp_sock.bind((host, port))

#create thread for heartbeat
heartbeat= threading.Thread(target = keepalive)
heartbeat.daemon = True
heartbeat.start()


if (len(sys.argv) == 4):
    inputs = [sys.stdin, udp_sock]
else:
    file_name_given = sys.argv[4]
    fd = open (file_name_given)
    inputs = [sys.stdin, udp_sock , fd]

while True:
    readable, writable, exceptional = select.select(inputs, [], [])
    for response in readable:
        if (udp_sock == response):
            number_of_messages+=1
            data = udp_sock.recv(1024)
            inp=data.split("~")
            count=int(inp[0])

#-----------------------gia tis metriseis-----------------------#
            dif = time.time()-float(inp[1])

            if(dif < 0 ):
                dif+=0.01
            endlatency+=dif
    #        print ("End latency:" + str(endlatency))
    #        print ("Number of msges:" + str(number_of_messages))

#----------------------------------------------------------------#

            output=inp[2]
            info=output.split(" ")
            group=info[1]
            user=info[2]
            if not data:
                print "Error receiving data"
                sys.exit()
            else:
                if(not user in mycounters[group]):
                    mycounters[group][user]=0
                if(mycounters[group][user]<=count):
                    mycounters[group][user]=count
                    sys.stdout.write('\n')
                    sys.stdout.write(output)
                    sys.stdout.write('\n')
                    sys.stdout.write("[%s]>" %username)
                    sys.stdout.flush()

        elif ( response==sys.stdin):
            line=response.readline()
            messages(line)

        else:

            if (flag == 1):
                line1= "!j distrib\n"
                flag=flag+1
                messages(line1)

            if (flag==2):
                line2= "!w distrib\n"
                flag=flag+1
                messages(line2)
            start=time.time()
            counter =0
            for line in fd:
                counter=counter+1
                if ( counter >=10 ):
                   data = line [3::]
                   if(counter == 50):
                       end=time.time()
                       message_time=end-start
#gia tis metriseis	   print ("Throughput : "  + str (message_time) )
#gia tis metriseis	   print ("Cost : " + str(cost))

                else:
                    data = line [2::]
                messages(data)
#                time.sleep(1)
