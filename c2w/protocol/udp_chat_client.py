# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
import logging
from c2w.main.client_proxy import c2wClientProxy
import struct
from twisted.internet import reactor
from twisted.internet import task
from c2w.main.constants import ROOM_IDS

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
        self.TokenHaveToWait=[]
        self.SequenceNumber=0
        self.ServerSN=0
        self.SessionToken=0
        self.RoomsIds=[]
        self.UserId=None
        self.UserName=None
        self.IdNames=[]
        self.ResetSN=False

    def startProtocol(self):
        """
        DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

        If in doubt, do not add anything to this method.  Just ignore it.
        It is used to randomly drop outgoing packets if the -l
        command line option is used.
        """
        self.transport = LossyTransport(self.transport, self.lossPr)
        DatagramProtocol.transport = self.transport

    def Reemission(self,Message,SessionToken,SequenceNumber):
        
        for i in self.TokenHaveToWait:
            if (i[0],i[1])==(SessionToken,SequenceNumber):
                if i[3]>3:
                    self.clientProxy.applicationQuit()
                    pass                 
                self.transport.write(Message,(self.serverAddress,self.serverPort))
                i[3]+=1
                reactor.callLater(1,self.Reemission,Message,SessionToken,SequenceNumber)



    def sendLoginRequestOIE(self, userName):
        """
        :param string userName: The user name that the user has typed.

        The client proxy calls this function when the user clicks on
        the login button.
        """
        moduleLogger.debug('loginRequest called with username=%s', userName)
        
        Version=1
        Type=1
        SessionToken=0
        SequenceNumber=0
        userName=userName.encode('utf-8')
        UserName=struct.pack('>H'+str(len(userName))+'s',len(userName),userName)
        Payload=struct.pack('>H'+str(len(UserName))+'s',0,UserName)
        PayloadSize=len(Payload)
        LRQ=struct.pack('>BBHHH'+str(PayloadSize)+'s',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*SessionToken//(2**16),SequenceNumber,PayloadSize,Payload)
        self.transport.write(LRQ,(self.serverAddress,self.serverPort))
        self.TokenHaveToWait.append([SessionToken,SequenceNumber,1,1]) #(ST,SN,Type,Iter)
        
        ########Prepare reemission#########################################################################
        
        reactor.callLater(1,self.Reemission,LRQ,SessionToken,SequenceNumber)
        

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
           client(s) doc/c2w.htmlwho are in the same room.
        """

        Version=1
        Type=6
        SessionToken=self.SessionToken
        self.SequenceNumber+=1
        SequenceNumber=self.SequenceNumber
        message=message.encode('utf-8')
        Payload=struct.pack('>HH'+str(len(message))+'s',self.UserId,len(message),message)
        PayloadSize=len(Payload)
        MSG=struct.pack('>BBHHH'+str(PayloadSize)+'s',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize,Payload)
        self.transport.write(MSG,(self.serverAddress,self.serverPort))
        self.TokenHaveToWait.append([SessionToken,SequenceNumber,0,1])

        ########Prepare reemission#########################################################################
        
        reactor.callLater(1,self.Reemission,MSG,SessionToken,SequenceNumber)

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

        Version=1
        Type=5
        SessionToken=self.SessionToken
        SequenceNumber=self.SequenceNumber
        self.SequenceNumber+=1
        PayloadSize=2
        RoomID=0
        for i in self.RoomsIds:
            if i[0]==roomName:
                RoomID=i[1]
        GTR=struct.pack('>BBHHHH',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize,RoomID)
        self.transport.write(GTR,(self.serverAddress,self.serverPort))
        self.TokenHaveToWait.append([SessionToken,SequenceNumber,5,1])
        
        ########Prepare reemission#########################################################################
        
        reactor.callLater(1,self.Reemission,GTR,SessionToken,SequenceNumber)
        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
        Version=1
        Type=7
        SessionToken=self.SessionToken
        SequenceNumber=self.SequenceNumber
        self.SequenceNumber+=1
        PayloadSize=0
        LOR=struct.pack('>BBHHH',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize)
        self.transport.write(LOR,(self.serverAddress,self.serverPort))
        self.TokenHaveToWait.append([SessionToken,SequenceNumber,7,1])

        ########Prepare reemission#########################################################################
        
        reactor.callLater(1,self.Reemission,LOR,SessionToken,SequenceNumber)

        pass

    def datagramReceived(self, datagram, host_port):
        """
        :param string datagram: the payload of the UDP packet.
        :param host_port: a touple containing the source IP address and port.

        Called **by Twisted** when the client has received a UDP
        packet.
        """
        ##########Reception################################################################################################################

        Data=struct.unpack('>BBHHH'+str(len(datagram)-8)+'s',datagram)
        Version,Type,SessionToken,SequenceNumber,PayloadSize,Payload=Data[0]//(2**4),Data[0]-(2**4)*(Data[0]//(2**4)),Data[1]*2**16+Data[2],Data[3],Data[4],Data[5]
        
        ##########Acknowledgement##########################################################################################################   

        if Type!=0:
            
            ACK=struct.pack('>BBHHH',16,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,0)
            self.transport.write(ACK,host_port)
            self.ServerSN=SequenceNumber
            self.ResetSN=False
            if self.ServerSN==65535:
                self.ResetSN=True
            
        ##########Traitement ACK et WaitList##########################################################################################################
        
        if Type==0:
            for i in self.TokenHaveToWait:
                if (i[0],i[1])==(SessionToken,SequenceNumber):
                    Type=i[2]
                    self.TokenHaveToWait.remove([SessionToken,SequenceNumber,Type,i[3]])

        ##########Traitement LRP#####################################################################################################################

        if Type==2:
            
            self.SessionToken=SessionToken
            Payload=struct.unpack('>B'+str(len(Payload)-1)+'s',Payload)
            ResponseCode=Payload[0]
            User=struct.unpack('>H'+str(len(Payload[1])-2)+'s',Payload[1])
            self.UserData=User
            self.UserId=User[0]
            self.UserName=User[1]
            userName=struct.unpack('>H'+str(len(User[1])-2)+'s',User[1])[1].decode('utf-8')
            if ResponseCode==3:
                self.clientProxy.connectionRejectedONE('This username already exists')
            if ResponseCode==2:
                self.clientProxy.connectionRejectedONE('This username is too long')
            if ResponseCode==4:
                self.clientProxy.connectionRejectedONE('The server is not available')
         
        ##########Traitement RST######################################################################################################################

        if Type==4:
            (RoomId,Payload)=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            (RoomNameSize,Payload)=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            (RoomName,Payload)=struct.unpack('>'+str(RoomNameSize)+'s'+str(len(Payload)-RoomNameSize)+'s',Payload)
            RoomName=RoomName.decode('utf-8')
            self.RoomsIds.append((RoomName,RoomId))
            if RoomName=='Main Room':
                    RoomName=ROOM_IDS.MAIN_ROOM
            (MovieIP,MoviePort,UserListSize,Payload)=struct.unpack('>IHH'+str(len(Payload)-8)+'s',Payload)
            userList=[]
            for i in range(UserListSize):
                (UserId,UserNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
                (UserName,Payload)=struct.unpack('>'+str(UserNameSize)+'s'+str(len(Payload)-UserNameSize)+'s',Payload)
                UserName=UserName.decode('utf-8')
                userList.append((UserName,RoomName))
                self.IdNames.append((UserId,UserName))
            (RoomListSize,Payload)=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            movieList=[]
            for i in range(RoomListSize):
                (RoomId,RoomNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
                (RoomName,Payload)=struct.unpack('>'+str(RoomNameSize)+'s'+str(len(Payload)-RoomNameSize)+'s',Payload)
                RoomName=RoomName.decode('utf-8')
                self.RoomsIds.append((RoomName,RoomId))
                if RoomName=='Main Room':
                    RoomName=ROOM_IDS.MAIN_ROOM
                (MovieIP,MoviePort,UserListSize,Payload)=struct.unpack('>IHH'+str(len(Payload)-8)+'s',Payload)
                a=MovieIP//(2**24)
                b=(MovieIP-a*2**24)//(2**16)
                c=(MovieIP-a*2**24-b*2**16)//(2**8)
                d=(MovieIP-a*2**24-b*2**16-c*2**8)
                MovieIP=str(a)+'.'+str(b)+'.'+str(c)+'.'+str(d)
                MoviePort=str(MoviePort)
                movieList.append((RoomName,MovieIP,MoviePort))
                for i in range(UserListSize):
                    (UserId,UserNameSize,Payload)=struct.unpack('>HH'+str(len(Payload)-4)+'s',Payload)
                    (UserName,Payload)=struct.unpack('>'+str(UserNameSize)+'s'+str(len(Payload)-UserNameSize)+'s',Payload)
                    UserName=UserName.decode('utf-8')
                    self.IdNames.append((UserId,UserName))                  
                    userList.append((UserName,RoomName))
                (RoomListSize,Payload)=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            if SequenceNumber==1:
                self.clientProxy.initCompleteONE(userList,movieList)
            else:
                self.clientProxy.setUserListONE(userList)
                
            
        ############Change Room after ACK############################################################################################################ 
       
        if Type==5:
    
            self.clientProxy.joinRoomOKONE()
            

        #############MSG Traitement###################################################################################################################
                     
        
        if Type==6:

            (UserId,MessageSize,Message)=struct.unpack('>HH'+str(PayloadSize-4)+'s',Payload)
            Message=Message.decode('utf-8')
            for User in self.IdNames:
                if User[0]==UserId:
                    UserName=User[1]
            self.clientProxy.chatMessageReceivedONE(UserName,Message)


        if Type==7:

            self.clientProxy.leaveSystemOKONE()





            


        pass
