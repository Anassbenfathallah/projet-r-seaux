# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
import logging
from c2w.main.client_proxy import c2wClientProxy
from struct import *
from c2w.main.constants import ROOM_IDS
import struct
logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_client_protocol')

############################################# functions #############################################################

def decodeIPAddress(encodedIP):
    struct.unpack('>BBBB',encodedIP)
    x,y,z,a=int("{0:b}".format(encodedIP[0]),2),int("{0:b}".format(encodedIP[1]),2),int("{0:b}".format(encodedIP[2]),2),int("{0:b}".format(encodedIP[3]),2)
    return str(x)+'.'+str(y)+'.'+str(z)+'.'+str(a)
def decodeRSTPayload(rstPayload):
    
    """ first we are going to see the users in the main room """
    UserId={}
    UserListMainRoom=[]
    UserListMovieRoom=[]
    movieList=[]
    UsersinMainRoom=struct.unpack('>HH'+str(len('main room'))+'sIHH'+str(len(rstPayload)-21)+'s',rstPayload)
    nbrofUsers=UsersinMainRoom[5]
    nbrofUsersINT=int("{0:b}".format(nbrofUsers),2)
    restOfPayload=UsersinMainRoom[6]
    
    for i in range(nbrofUsersINT):
        UserListMainRoom.append(getname(restOfPayload)[0])
        userID=getname(restOfPayload)[2]
        restOfPayload=getname(restOfPayload)[1]
        
        UserId[userID]=UserListMainRoom[-1]
    lengthofMovies=struct.unpack('>H'+str(len(restOfPayload)-2)+'s',restOfPayload)[0]
    
    restOfPayload=struct.unpack('>H'+str(len(restOfPayload)-2)+'s',restOfPayload)[1]
    
    
    PayloadMovieInfo=restOfPayload
    
    """ a loop of 5 times to get users in the 5 other rooms the same way we got those in main room"""
    for i in range(lengthofMovies):
        movieList.append(getMovieInfo(restOfPayload)) ##here we get the info of the movies 'name' 'ip' 'port'
        movieName=movieList[i][0]
        if len(restOfPayload)-12-len(getMovieInfo(restOfPayload))<=0:
            UserListMovieRoom.append([[]])     
        else :
            UsersinMovieRoom=struct.unpack('>HH'+str(len(getMovieInfo(restOfPayload)[0]))+'sIHH'+str(len(restOfPayload)-12-len(getMovieInfo(restOfPayload)[0]))+'s',restOfPayload)
            nbrofUsersMovieRoom=UsersinMovieRoom[5]
            nbrofUsersMovieRoomINT=nbrofUsersMovieRoom
            restOfPayload=UsersinMovieRoom[6]
        
            for j in range(nbrofUsersMovieRoomINT):
                userID=getname(restOfPayload)[2]
                UserListMovieRoom.append((getname(restOfPayload)[0],movieName))
                restOfPayload=splitPayload(restOfPayload)[1]
                UserId[userID]=UserListMovieRoom[-1][0]
            if i!=4:
                restOfPayload=struct.unpack('>H'+str(len(restOfPayload)-2)+'s',restOfPayload)[1]
    userList=[]
    for i in UserListMainRoom:
        userList.append((i,ROOM_IDS.MAIN_ROOM))
    for i in UserListMovieRoom:
        userList.append(i)
    
    return (userList,movieList,UserId)
    
    
    
     
def splitPayload(payload):
    Split=struct.unpack('>HH'+str(len(payload)-4)+'s',payload)
    lenString=Split[1]
    newsplit=struct.unpack('>'+str(4+lenString)+'s'+str(len(payload)-lenString-4)+'s',payload)
    return (newsplit[0],newsplit[1])
    
    
def getMovieInfo(rst):
     ##our rst here starts with 4 bytes then the bytes of the string of the movie name, we can use then the function getname, to get the movie title
    if len(rst)<=2:
        roomID=255
        movieName='Error'
        movieIP='0'   
        moviePort=0  
    else :
        roomID=struct.unpack('>H'+str(len(rst)-2)+'s',rst)[0]
        TheSplit=splitPayload(rst)
        movieName=getnameandid(TheSplit[0])[1]
        restOfRST=TheSplit[1]
        roomID=getnameandid(TheSplit[0])[0]
        EncodedIp=restOfRST[0:4]
        movieIP=decodeIPAddress(EncodedIp)
        moviePort=struct.unpack('>H',restOfRST[4:6])[0]
    return (movieName,movieIP,str(moviePort),roomID)
    

def getnameandid(payload):
    allname=struct.unpack('>HH'+str(len(payload)-4)+'s',payload)
    usrid=allname[0]
    lenName=allname[1]
    userName=allname[2].decode('utf-8')
    return (usrid,userName)
    


def getname(payload):  ##the payload here has 4 bytes then the bytes of the string we want to get
    lenUsername=struct.unpack('>HH'+str(len(payload)-4)+'s',payload)
    Userid=lenUsername[0]
    lenUsernameINT=lenUsername[1]
    
    if lenUsernameINT<len(lenUsername[2]):
        userName=struct.unpack('>'+str(lenUsernameINT)+'s'+str(len(lenUsername[2])-lenUsernameINT)+'s',lenUsername[2])[0].decode('utf-8')
        payloadwithNoUsername=struct.unpack('>'+str(lenUsernameINT)+'s'+str(len(lenUsername[2])-lenUsernameINT)+'s',lenUsername[2])[1]
    elif lenUsernameINT>=len(lenUsername[2]):
        userName=struct.unpack('>'+str(lenUsernameINT)+'sHH',lenUsername[2])[0].decode('utf-8')
        payloadwithNoUsername=struct.unpack('>'+str(lenUsernameINT)+'sHH',lenUsername[2])[1]
    return (userName,payloadwithNoUsername,Userid)


###############################the class############################
class c2wUdpChatClientProtocol(DatagramProtocol):
    UserIdDict={}
    
    def __init__(self, serverAddress, serverPort, clientProxy, lossPr,lastSequenceNumberSentJR=None,lastSequenceNumberSentLS=None):
        """
        :param serverAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param serverPort: The port number used by the c2w server,
            given by the user.
        :param clientProxy: The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attributes:

        .. attribute:: serverAddress

            The IP address of the c2w server.

        .. attribute:: serverPort

            The port number of the c2w server.

        .. attribute:: clientProxy

            The clientProxy, which the protocol must use
            to interact with the Graphical User Interface.

        .. attribute:: lossPr

            The packet loss probability for outgoing packets.  Do
            not modify this value!  (It is used by startProtocol.)

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """

        #: The IP address of the c2w server.
        self.serverAddress = serverAddress
        #: The port number of the c2w server.
        self.serverPort = serverPort
        #: The clientProxy, which the protocol must use
        #: to interact with the Graphical User Interface.
        self.clientProxy = clientProxy
        self.lossPr = lossPr
        self.SequenceNumber=0
        self.UserId=0
        self.SessionToken=0
        self.movieList=[]
        self.lastSequenceNumberSentJR=lastSequenceNumberSentJR
        self.lastSequenceNumberSentLS=lastSequenceNumberSentLS
        
    def startProtocol(self):
        """
        DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

        If in doubt, do not add anything to this method.  Just ignore it.
        It is used to randomly drop outgoing packets if the -l
        command line option is used.
        """
        self.transport = LossyTransport(self.transport, self.lossPr)
        DatagramProtocol.transport = self.transport

    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The client proxy calls this function when the user clicks on
        the login button.
        """

       
        Version=1
        Type=1
        usName=userName.encode('utf-8')
        uName=struct.pack('>H'+str(len(usName))+'s',len(usName),usName)
        Payload=struct.pack('>H'+str(len(uName))+'s',0,uName)
        Psize=len(Payload)
        LoginRequest=struct.pack('>BBHHH'+str(Psize)+'s',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,Psize,Payload)
        self.transport.write(LoginRequest,(self.serverAddress,self.serverPort))

        #Version=1
        #Type=1
        #SessionToken=0
        #SequenceNumber=0
        #userName=userName.encode('utf-8')
        #UserName=struct.pack('>H'+str(len(userName))+'s',len(userName),userName)
        #Payload=struct.pack('>H'+str(len(UserName))+'s',0,UserName)
        #PayloadSize=len(Payload)
        #LRQ=struct.pack('>BBHHH'+str(PayloadSize)+'s',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*SessionToken//(2**16),SequenceNumber,PayloadSize,Payload)
        #self.transport.write(LRQ,(self.serverAddress,self.serverPort))




	
	


	

    def sendChatMessageOIE(self, message):
        """
        :param message: The text of the chat message.
        :type message: string

        Called by the client proxy  when the user has decided to send
        a chat message

        .. note::
           This is the only function handling chat messages, irrespective
           of the room where the user is.  Therefore it is up to the
           c2wChatClientProctocol or to the server to make sure that this
           message is handled properly, i.e., it is shown only by the
           client(s) who are in the same room.
        """
        Version=1
        Type=6
        Message=message.encode('utf-8')
        print('SM'+ str(self.SessionToken))
        Pld=struct.pack('>HH'+str(len(Message))+'s',self.UserId,len(Message),Message)
        PldSize=len(Pld)
        print(PldSize)
        ChatMessage=struct.pack('>BBHHH'+str(PldSize)+'s',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,PldSize,Pld)
        self.transport.write(ChatMessage,(self.serverAddress,self.serverPort))
        pass

    def sendJoinRoomRequestOIE(self, roomName):
        """
        :param roomName: The room name (or movie title.)

        Called by the client proxy  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            The controller sets roomName to
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        if roomName==ROOM_IDS.MAIN_ROOM:
            roomID=1
        else:
            for i in self.movieList:
                if i[0]==roomName:
                    roomID=i[3]
        Version=1
        Type=5
        
        self.lastSequenceNumberSentJR=self.SequenceNumber
        print('JR'+ str(self.SessionToken))
        print(self.SequenceNumber)
        
        GTR=struct.pack('>BBHHHH',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,2,roomID)
        self.transport.write(GTR,(self.serverAddress,self.serverPort))

        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
        Version=1
        Type=7
        
        self.lastSequenceNumberSentLS=self.SequenceNumber
        LOR=struct.pack('>BBHHH',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,0)
        self.transport.write(LOR,(self.serverAddress,self.serverPort))

        pass

    def datagramReceived(self, datagram, host_port):
        """
        :param string datagram: the payload of the UDP packet.
        :param host_port: a touple containing the source IP address and port.

        Called **by Twisted** when the client has received a UDP
        packet.
        """

        Packet=struct.unpack('>BBHHH'+str(len(datagram)-8)+'s',datagram) 
        Version=Packet[0]//(2**4)
        Type=Packet[0]-(2**4)*(Packet[0]//(2**4))
        self.SessionToken=Packet[1]*(2**16)+Packet[2]
        self.SequenceNumber=Packet[3]
        print(self.SessionToken)
        PayloadSize=Packet[4]
        Payload=Packet[5]

        if Type==0 : 
            if self.SequenceNumber==self.lastSequenceNumberSentJR:
                #print('me here' + str(self.SessionToken))
                self.clientProxy.joinRoomOKONE()
                self.RRS()
            if self.SequenceNumber==self.lastSequenceNumberSentLS:
                self.clientProxy.leaveSystemOKONE()
                #self.RRS()
                
                 
        if Type!=0:## if the datagram isn't an ACK we have to send one to the server
            Ack=struct.pack('>BBHHH',16,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,0)
            self.transport.write(Ack,host_port)
        if Type==2 :
            #print(self.SessionToken)
            self.UserId=struct.unpack('>BH'+str(len(Payload)-3)+'s',Payload)[1]
            ResponseCode=struct.unpack('>B'+str(len(Payload)-1)+'s',Payload)[0]
            respCode=int("{0:b}".format(ResponseCode),2)
            if respCode==2:
                self.clientProxy.connectionRejectedONE('Connection failed : Username too long!')
            if respCode==1:
                self.clientProxy.connectionRejectedONE('Connection failed : invalid Username!')
            if respCode==3:
                self.clientProxy.connectionRejectedONE('Connection failed : Username already taken!')
            if respCode==4:
                self.clientProxy.connectionRejectedONE('Connection failed : Service not available!')
        if Type==4 and self.SequenceNumber==1 :
            c2wUdpChatClientProtocol.UserIdDict=decodeRSTPayload(Payload)[2]
            (userList,self.movieList)=decodeRSTPayload(Payload)[0:2]
            
            self.clientProxy.initCompleteONE(userList,self.movieList)
        if Type==4 and self.SequenceNumber!=1 :
            c2wUdpChatClientProtocol.UserIdDict=decodeRSTPayload(Payload)[2]
            userList=decodeRSTPayload(Payload)[0]
            print(userList)
            self.clientProxy.setUserListONE(userList) 
            #print(self.SessionToken)
        if Type==6 :
            
            MessageandId=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
            Message=MessageandId[2].decode('utf-8')
            Id=MessageandId[0]
            Idint=int("{0:b}".format(Id),2)
            
            username=c2wUdpChatClientProtocol.UserIdDict[Idint]
            print('me'+str(username))
            self.clientProxy.chatMessageReceivedONE(username,Message)
        if Type==3 :
            userList=decodeRSTPayload(Payload)[0]
            c2wUdpChatClientProtocol.UserIdDict=decodeRSTPayload(Payload)[2]
            for user in userList:
                self.clientProxy.userUpdateReceivedONE(user[0],user[1]) 
            
    def RRS(self):
        Version=1
        Type=3
        self.SequenceNumber+=1
        RRS=struct.pack('>BBHHH',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,0)
        self.transport.write(RRS,(self.serverAddress,self.serverPort))
                
            


        pass
