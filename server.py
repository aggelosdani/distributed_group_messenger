import time
import zmq
import uuid
import threading


flag=0
clients_data = {}
groups_members = {}
groups = []
lock = threading.Lock()

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:5555")

alive_clients={}

def heartbeat():

    while True:
        dead_clients = []
        with lock:
            for client_id in alive_clients:
                count_time = time.clock()
                if (alive_clients[client_id] < count_time - 0.01):
                    dead_clients.append(client_id)
            if (dead_clients != []):
                for client_id in dead_clients:
                    print ("Dead client: "+ client_id)
                    del alive_clients[client_id]
                    previous_groups = groups[:]
                    for group_name in previous_groups:
                        if (client_id in groups_members[group_name]):
                            groups_members [group_name].remove(client_id)
                            if (groups_members[group_name] == []):
                                del groups_members[group_name]
                                groups.remove(group_name)

        time.sleep(20)

## heartbeat hread
check_thread = threading.Thread(target = heartbeat)
check_thread.daemon = True
check_thread.start()




while True:

    message = socket.recv()

            #######--------TRACKER-------#############

    if (message.startswith('!')):
        #######---- Checking if we write a command or not.-----#######

        temp = message.split(' ')
        command = temp[0].lstrip('!')
        args_size = len(temp) - 1

        if(command=="heartbeat"):
            with lock:
                alive_clients[temp[1]]=time.clock()


        #######-------Checking for argument errors---------- #######

        if (command == "r" and args_size != 3):
            flag=1
            command= "*Invalid arguments"
            args=[]
        elif (command == "lg" and args_size != 1):
            flag=1
            command= "*Invalid arguments"
            args=[]
        elif (command == "lm" and args_size != 2):
            flag=1
            command= "*Invalid arguments"
            args=[]
        elif (command == "j" and args_size != 2):
            flag=1
            command= "*Invalid arguments"
            args=[]
        elif (command == "e" and args_size != 2):
            flag=1
            command= "*Invalid arguments"
            args=[]
        elif (command == "q " and args_size != 1):
            flag=1
            command= "*Invalid arguments"
            args=[]
        elif(command=="a"and args_size !=2):
            flag=1
            args=[]

        args = temp [1:]
        ###If there is an argument error make flag=1 and reply= Invalid message###

    else:
        command = []
        args = []
        flag=1

    if (flag== 0):
        if (command == "r"):
            unique_id= uuid.uuid4()
            id = str(unique_id)
            clients_data[id] = (args[0], args[1], args[2])
            print "New client connected: ", id
            with lock:
                alive_clients[id]=time.clock()
            reply=id


#-----------------------------------------------------------------#

        elif (command == "lg"):


            print "Active groups are: ", groups
            reply =  str(groups)

#-----------------------------------------------------------------#
        elif (command == "lm"):

            if (not groups_members.has_key(args[0])):
                usernames_group= []
            else:
                members_ids = groups_members[args[0]]
                members_names = []
                for member_id in members_ids:
                    _, _, name = clients_data[member_id]
                    members_names.append(name)
                print "Members in group: " + args[0] + ": ", str(members_names)

                usernames_group = members_names

            reply = str(usernames_group) if usernames_group else "*List of Members"

#-----------------------------------------------------------------#


        elif (command == "j"):
            temp=True
            # create group if not exists
            if (not groups_members.has_key(args[0])):
                groups_members[args[0]] = []
                groups.append(args[0])

            if args[1] not in groups_members[args[0]]:
                groups_members[args[0]].append(args[1])
            else:
                temp=False


            members_data = []
            for client_id in groups_members[args[0]]:
                members_data.append((client_id, ) + clients_data[client_id])

            reply = str(members_data) if temp else "*Already member of the group"

#-----------------------------------------------------------------#

        elif (command == "e"):

            exit= True
            if (not groups_members.has_key(args[0])):
                print "Group, not found"
                exit= False
            try:
                groups_members[args[0]].remove(args[1])
            except ValueError:
                print "Not a member of the requested group"
                exit= False

            # delete group if empty
            if (groups_members[args[0]] == []):
                del groups_members[args[0]]
                try:
                    groups.remove(args[0])
                except ValueError:
                    print "Group, not found"
                    exit= False



            reply = "Successfull exit" if exit else "*exit group"

#-----------------------------------------------------------------#

        elif (command == "q"):
            previous_groups = groups[:]
            exit= True

            # removing user from all groups
            for group_name in previous_groups:
                if (not groups_members.has_key(group_name)):
                    exit= False
                try:
                    groups_members [group_name].remove(args[0])
                except ValueError:
                    exit= False

                if (groups_members[group_name] == []):
                    del groups_members[group_name]
                    try:
                        groups.remove(group_name)
                    except ValueError:
                        exit= False


            reply = "Successfull quit" if exit else "*Quit"

#-----------------------------------------------------------------#

        elif(command=="u"):
            group_name=temp[1]
            members = []
            for client_id in groups_members[group_name]:
                members.append((client_id, ) + clients_data[client_id])
            reply=str(members)

#------------------------------------------------------------------#

        else:
            reply = "*Invalid command"

    flag=0
    #  Send reply back to client
    socket.send(reply)
