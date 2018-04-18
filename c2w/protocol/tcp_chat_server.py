# -*- coding: utf-8 -*-
from twisted.internet.protocol import Protocol
import logging

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.tcp_chat_server_protocol')
import struct
import random
from c2w.main.constants import ROOM_IDS
from c2w.main.server_proxy import c2wServerProxy
from twisted.internet import reactor

def encodeIPadress(IP):
    x,y,z,a=IP.split(".")
    return struct.pack('>BBBB',int(x),int(y),int(z),int(a))
class c2wTcpChatServerProtocol(Protocol):

    def __init__(self, serverProxy, clientAddress, clientPort):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
        :param clientAddress: The IP address (or the name) of the c2w server,
            given by the user.
        :param clientPort: The port number used by the c2w server,
            given by the user.

        Class implementing the TCP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: clientAddress

            The IP address of the client corresponding to this 
            protocol instance.

        .. attribute:: clientPort

            The port number used by the client corresponding to this 
            protocol instance.

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.

        .. note::
            The IP address and port number of the client are provided
            only for the sake of completeness, you do not need to use
            them, as a TCP connection is already associated with only
            one client.
        """
        #: The IP address of the client corresponding to this 
        #: protocol instance.
        self.clientAddress = clientAddress
        #: The port number used by the client corresponding to this 
        #: protocol instance.
        self.clientPort = clientPort
        #: The serverProxy, which the protocol must use
        #: to interact with the user and movie store in the server.
        self.serverProxy = serverProxy
        self.theData=b""
        self.allPayloadSize=0
        self.host_port=(clientAddress,clientPort)
        self.SessionToken=0
        self.SequenceNumber=0
        self.userID=0
        self.ACK=False
        self.c=0
        self.ce=0
        self.ACKofLRS=False
        self.sequenceNumberSentHello=None
        self.ACKLR=False
        self.sequenceNumberSentLR=None

    def dataReceived(self, data):
        """
        :param data: The data received from the client (not necessarily
                     an entire message!)

        Twisted calls this method whenever new data is received on this
        connection.
        """
        
        self.theData+=data
        
        if len(self.theData)>=8 :
            Packet=struct.unpack('>BBHHH'+str(len(self.theData)-8)+'s',self.theData)
            PayloadSize=Packet[4]
            print('me',Packet)
            
            
            self.allPayloadSize=PayloadSize
            if len(Packet[5])==self.allPayloadSize:
                
                AllPacket=self.theData[0:8+self.allPayloadSize]
                if self.allPayloadSize==0:
                    print('im here')
                    Packet=struct.unpack('>BBHHH',AllPacket)
                else:
                    Packet=struct.unpack('>BBHHH'+str(len(AllPacket)-8)+'s',AllPacket)
                    Payload=Packet[5]
                Version=Packet[0]//(2**4)
                Type=Packet[0]-(2**4)*(Packet[0]//(2**4))
                self.SessionToken=Packet[1]*(2**16)+Packet[2]
                
                PayloadSize=Packet[4]
                
                self.SequenceNumber=Packet[3]
                self.allPayloadSize=PayloadSize
                if Type==0:
                    print('heere')
                    if self.sequenceNumberSentHello==self.SequenceNumber:
                        self.ACK=True
                    if self.SequenceNumber==0 and self.SessionToken!=0:
                        print('got in')
                        self.ACKLR=True
              
            
                
          
         

                if Type!=0:## if the datagram isn't an ACK we have to send one to the client
                    Ack=struct.pack('>BBHHH',16,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,0)
                    self.transport.write(Ack)

                if Type==1 :
                    decodedLoginRequest=self.decodeLoginRequest(Payload,self.host_port)
                    ResponseCode,data=decodedLoginRequest[0],decodedLoginRequest[1]
                    self.loginResponse(ResponseCode,data)
                if Type==5:
                    roomID=struct.unpack('>H',Payload)[0]
            
                    user=self.serverProxy.getUserByAddress(self.host_port)
                
                    for movie in self.serverProxy.getMovieList():
                        if movie.movieId==roomID:
                            self.serverProxy.updateUserChatroom(user.userName,movie.movieTitle)
                    #self.serverProxy.startStreamingMovie(movie.movieTitle)
                    if roomID==1:
                #self.serverProxy.stopStreamingMovie(user.userChatRoom)
                        self.serverProxy.updateUserChatroom(user.userName,ROOM_IDS.MAIN_ROOM)
                
            
                    self.sendToAll(Version)
            #self.tokenSequenceList.append(SessionToken)
            #self.tokenSequenceList.append(SequenceNumber)
            #Packet=struct.unpack('>BBHHH'+str(len(datagram)-8)+'s',datagram)
            #Version=Packet[0]//2**4
            #Type=Packet[0]-Packet[0]//2**4 
            #SessionToken=Packet[1]*(2**16)+Packet[2]
            #SequenceNumber=Packet[3]
            #PayloadSize=Packet[4]
            #Payload=Packet[5]
                if Type==7 :
                    username=self.serverProxy.getUserByAddress(self.host_port).userName
                    self.serverProxy.removeUser(username)
                
            
                    self.sendToAll(Version)
            #self.sendToAll(Version)
                if Type==3 :
                    self.sendToAll(Version)
                if Type==6:
                    sender=self.serverProxy.getUserByAddress(self.host_port)
                    for user in self.serverProxy.getUserList():
                        if user.userAddress!=self.host_port and sender.userChatRoom==user.userChatRoom :
                    
                            c2wUdpChatServerProtocol.hostPortSequence[user.userAddress]+=1
                            sessionToken=c2wUdpChatServerProtocol.UserToken[user.userAddress]
                            Message=struct.pack('>BBHHH'+str(len(Payload))+'s',Version*2**4+Type,sessionToken//(2**16),sessionToken-(2**16)*(sessionToken//(2**16)),self.SequenceNumber,len(Payload),Payload)
                            self.transport.write(Message,user.userAddress)
                if self.SequenceNumber>=1 and self.serverProxy.getUserByAddress(self.host_port)!=False:
                    Hello=reactor.callLater(10,self.Hello,self.host_port)
                    if self.c==3 : 
               
                        username=self.serverProxy.getUserByAddress(self.host_port).userName
                        self.serverProxy.removeUser(username)
                        self.sendToAll(Version)
                if self.ACKLR==True :
                    self.sendToAll(Version)
                self.theData=self.theData[self.allPayloadSize+8:]
                
                self.allPayloadSize=0
    
    def decodeLoginRequest(self,Payload,host_port):
        uData=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
        uName=struct.unpack('H'+str(len(uData[1])-2)+'s',uData[1])
        userName=uName[1].decode('utf-8') 
        if self.SessionToken!=0:
            ResponseCode=1
            uData=struct.pack('>H'+str(len(uData[1]))+'s',0,uData[1])
        if len(userName)>100:
            ResponseCode=2
            uData=struct.pack('>H'+str(len(uData[1]))+'s',0,uData[1])

        elif self.serverProxy.userExists(userName)==True:  
            ResponseCode=3
            uData=struct.pack('>H'+str(len(uData[1]))+'s',0,uData[1])
            
           
        elif len(self.serverProxy.getUserList())>65535:
            ResponseCode=4
            uData=struct.pack('H'+str(len(uData[1]))+'s',0,uData[1])

        else:
            ResponseCode=0
            self.ce+=1
            print('yes')
            self.userID=self.serverProxy.addUser(userName,ROOM_IDS.MAIN_ROOM,None,host_port)
                
                
            self.SessionToken=random.getrandbits(24)
                
                
            uData=struct.pack('>H'+str(len(uData[1]))+'s',self.userID,uData[1])
        return(ResponseCode,uData)
    def loginResponse(self,ResponseCode,uData):
        self.sequenceNumberSentLR=self.SequenceNumber            
        Version=1
        Type=2
        Payload=struct.pack('>B'+str(len(uData))+'s',ResponseCode,uData)
        print(Payload)
        LoginResponse=struct.pack('>BBHHH'+str(len(Payload))+'s',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,len(Payload),Payload)
        self.transport.write(LoginResponse)
        print(LoginResponse)
            
        if ResponseCode==0 and self.ACKLR==True:
            print('here22')
            self.sendToAll(Version)                
    def sendToAll(self,Version):
        Type=4
        RST=self.RST('Main Room')
        
        
        for user in self.serverProxy.getUserList():
            self.SequenceNumber+=1
            
            sessionToken=self.SessionToken
            RSTall=struct.pack('>BBHHH',Version*2**4+Type,sessionToken//(2**16),sessionToken-(2**16)*(sessionToken//(2**16)),self.SequenceNumber,len(RST))+RST
            self.transport.write(RSTall)
        
                
    def RST(self,Rname):        
        if Rname=='Main Room':
            RST1=b""
            RoomID=1
            MovieIP=0
            MoviePort=0
            MovieL=self.serverProxy.getMovieList()
            UsersList=[]
            
            
            for User in self.serverProxy.getUserList():
                if User.userChatRoom==ROOM_IDS.MAIN_ROOM :
                    UsersList.append(struct.pack('>HH'+str(len(User.userName))+'s',User.userId,len(User.userName),User.userName.encode('utf-8')))
            Userlist=struct.pack('>H',len(UsersList))
            
            for user in UsersList :
                Userlist+=user
            for movie in MovieL:
                RST1+=self.RST(movie.movieTitle)
            RST=struct.pack('>HH'+str(len(Rname))+'sIH',RoomID,len(Rname),Rname.encode('utf-8'),MovieIP,MoviePort)+Userlist+struct.pack('>H',len(MovieL))+RST1
            
            return RST
        else :
            movie=self.serverProxy.getMovieByTitle(Rname)
            RoomId=movie.movieId
            MovieIP=movie.movieIpAddress
            MoviePort=movie.moviePort        
            MovieL=[]
            RoomName=struct.pack('>H'+str(len(Rname))+'s',len(Rname),Rname.encode('utf-8'))
            UsersList=[]
            for User in self.serverProxy.getUserList() :
                
                if User.userChatRoom==Rname or User.userChatRoom==ROOM_IDS.MOVIE_ROOM:
                    UsersList.append(struct.pack('>HH'+str(len(User.userName))+'s',User.userId,len(User.userName),User.userName.encode('utf-8')))
            Userlist=struct.pack('>H',len(UsersList))
            for user in UsersList :
                Userlist+=user
            
            return struct.pack('>H',RoomId)+RoomName+encodeIPadress(MovieIP)+struct.pack('>H',MoviePort)+Userlist+struct.pack('>H',len(MovieL))
    def Hello(self,host_port):

        
        ##for user in self.serverProxy.getUserList():
            #if user.userAddress==host_port:
                #username=user.userName
        if self.serverProxy.getUserByAddress(host_port)!=False :
            print('yes')
            self.SequenceNumber+=1
            sessionToken=self.SessionToken
            self.sequenceNumberSentHello=self.SequenceNumber
            Version=1
            Type=8
            self.c+=1
            Hello=struct.pack('>BBHHH',Version*2**4+Type,self.SessionToken//(2**16),sessionToken-(2**16)*(sessionToken//(2**16)),self.SequenceNumber,0)
            self.transport.write(Hello)
          
            if self.c<=3:
                if self.ACK==False : 
                    self.SequenceNumber=self.SequenceNumber-1    
                    reactor.callLater(10,self.Hello,host_port)
        pass
