# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
import logging
from c2w.main.client_proxy import c2wClientProxy
from struct import *
import struct
logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_client_protocol')


class c2wUdpChatClientProtocol(DatagramProtocol):

    def __init__(self, serverAddress, serverPort, clientProxy, lossPr):
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
        self.Rooms=[]
        self.NamesID=[]
        self.UserId=0
        self.Token=0
        self.SeqNumber=0


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

        usName=userName.encode('utf-8')
        Payload=struct.pack('>H'+str(len(uName))+'s',0,uName)
        PSize=len(Payload)
        uName=struct.pack('>H'+str(len(usName))+'s',len(usName),usName)
        SeqNumber=0
        Token=0
        Type=1
        Version=1     
        LoginRequest=struct.pack('>BBHHH'+str(PSize)+'s',Version*2**4+Type,Token//(2**16),Token-(2**16)*Token//(2**16),SeqNumber,PSize,Payload)
        self.transport.write(LoginRequest,(self.serverAddress,self.serverPort))

        

	
	


	

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
           client(s) who are in the same room."""
        SeqNumber=self.SeqNumber
        self.SeqNumber=self.SeqNumber+1
        Token=self.Token
        Type=6
        Version=1
        Mess=message.encode('utf-8')
        Payload=struct.pack('>H'+str(len(Mess))+'s',self.UserID,Mess)
        PSize=len(Payload)
        Message=struct.pack('>BBHHH'+str(PSize)+'s',Version*2**4+Type,Token//(2**16),Token-(2**16)*(Token//(2**16)),SeqNumber,PSize,Payload)
        self.transport.write(Message,(self.serverAddress,self.serverPort))
        pass

    def sendJoinRoomRequestOIE(self, roomName):
        """
        :param roomName: The room name (or movie title.)

        Called by the client proxy  when the user
        has clicked on the watch button or the leave button,
        indicating that she/he wants to change room.

        .. warning:
            c2w.main.constants.ROOM_IDS.MAIN_ROOM when the user
            wants to go back to the main room.
        """
        SeqNumber=self.SeqNumber
        self.SeqNumber=self.SeqNumber+1
        SeqNumber=self.SeqNumber
        Token=self.Token
        Type=5      
        Version =1
        
        PSize=2
        RoomID=0
        for i in self.Rooms:
            if i[0]==roomName:
                RoomID=i[1]
        GoToRoom=struct.pack('>BBHHHH',Version*2**4+Type,Token//(2**16),Token-(2**16)*(Token//(2**16)),SeqNumber,PSize,RoomID)
        self.transport.write(GoToRoom,(self.serverAddress,self.serverPort))
        
        

        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
        self.SeqNumber=self.SeqNumber+1 
        Token=self.Token
        Type=7       
        Version=1
        
        PSize=0
        LeaveMessage=struct.pack('>BBHHH',Version*2**4+Type,Token//(2**16),Token-(2**16)*(Token//(2**16)),SeqNumber,PSize)
        self.transport.write(LeaveMessage,(self.serverAddress,self.serverPort))
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
        Token=Packet[1]*(2**16)+Packet[2]
        SeqNumber=Packet[3]
        PSize=Packet[4]
        Payload=Packet[5]

   
        if Type!=0:## if the datagram isn't an ACK we have to send one to the client
            
            Ack=struct.pack('>BBHHH',16,Token//(2**16),Token-(2**16)*(Token//(2**16)),SeqNumber,0)
            self.transport.write(Ack,host_port)

        if Type==2 :
            Data=struct.unpack('>B'+str(len(Payload)-1)+'s',Payload)
            RespCode=Data[0]
            User=struct.unpack('H'+str(len(Data[1])-2)+'s',Data[1])
            UserId=User[0]
            userName=struct.unpack('>H'+str(len(User[1])-2)+'s',User[1])[1].decode('utf-8')
            if RespCode == 1 :
                self.clientProxy.connectionRejectionONE('Invalid Use')
            elif RespCode == 2 :
                self.clientProxy.connectionRejectedONE('Username too long')
            elif RespCode ==3 :
                self.clientProxy.connectionRejectedONE('Username not available')
            elif RespCode == 4 :
                self.clientProxy.connectionRejectedONE('Service not available')

        if Type==4:
            Users=[]
            (RoomID,RoomNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
            (RoomName,Payload)=struct.unpack('>'+str(RoomNameSize)+'s'+str(len(Payload)-RoomNameSize)+'s',Payload)
            (MovieIP,MoviePort,UserListSize,Payload)=struct.unpack('>IHH'+str(len(Payload)-8)+'s',Payload)
            RoomName=RoomName.decode('utf-8')
            self.Rooms.append((RoomName,RoomID))
            for i in range(UserListSize) : 
                (UserId,UserNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
                (UserName,Payload)=struct.unpack('>'+str(UserNameSize)+'s'+str(len(Payload)-UserNameSize)+'s',Payload)
                UserName=UserName.decode('utf-8')
                Users.append((UserName,RoomName))
                self.NamesID.append((UserId,UserName))
            (RoomListSize,Payload)=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            movieList=[]
            for i in range(RoomListSize):
                (RoomID,RoomNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
                (RoomName,Payload)=struct.unpack('>'+str(RoomNameSize)+'s'+str(len(Payload)-RoomNameSize)+'s',Payload)
                (MovieIP,MoviePort,UserListSize,Payload)=struct.unpack('>IHH'+str(len(Payload)-8)+'s',Payload)
                RoomName=RoomName.decode('utf-8')
                self.Rooms.append((RoomName,RoomID))  
                movieList.append((RoomName,MovieIP,MoviePort))
                for i in range(UserListSize):
                    (UserID,UserNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
                    (UserName,Payload)=struct.unpack('>'+str(UserNameSize)+'s'+str(len(Payload)-UserNameSize)+'s',Payload)
                    UserName=UserName.decode('utf-8')
                    self.IdNames.append((UserId,UserName))                  
                    Users.append((UserName,RoomName))
                (RoomListSize,Payload)=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload) 
            if SeqNumber==1:
                self.clientProxy.initCompleteONE(Users,movieList)
            else:
                self.clientProxy.setUserListONE(Users)


        if Type==5:
    
            self.clientProxy.joinRoomOKONE()

        if Type==6:
            (UserId,MessageSize,Message)=struct.unpack('>HH'+str(PSize-4)+'s',Payload)
            MSG=Message.decode('utf8')
            for User in self.NamesID:
                if User[0]==UserId:
                    UserName=User[1]
            self.clientProxy.chatMessageReceivedONE(UserName,Message)


        if Type==7:

            self.clientProxy.leaveSystemOKONE()
        
              
              
          
            
            
            



        pass
