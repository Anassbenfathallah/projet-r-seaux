# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
import logging
import struct
import random

logging.basicConfig()
moduleLogger = logging.getLogger('c2w.protocol.udp_chat_server_protocol')


class c2wUdpChatServerProtocol(DatagramProtocol):

    def __init__(self, serverProxy, lossPr):
        """
        :param serverProxy: The serverProxy, which the protocol must use
            to interact with the user and movie store (i.e., the list of users
            and movies) in the server.
        :param lossPr: The packet loss probability for outgoing packets.  Do
            not modify this value!

        Class implementing the UDP version of the client protocol.

        .. note::
            You must write the implementation of this class.

        Each instance must have at least the following attribute:

        .. attribute:: serverProxy

            The serverProxy, which the protocol must use
            to interact with the user and movie store in the server.

        .. attribute:: lossPr

            The packet loss probability for outgoing packets.  Do
            not modify this value!  (It is used by startProtocol.)

        .. note::
            You must add attributes and methods to this class in order
            to have a working and complete implementation of the c2w
            protocol.
        """
        #: The serverProxy, which the protocol must use
        #: to interact with the server (to access the movie list and to 
        #: access and modify the user list).
        self.serverProxy = serverProxy
        self.lossPr = lossPr
        self.SessionToken=random.getrandbits(24)
        self.tokenSequenceList=[]
        self.SequenceNumber=0

    def startProtocol(self):
        """
        DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

        If in doubt, do not add anything to this method.  Just ignore it.
        It is used to randomly drop outgoing packets if the -l
        command line option is used.
        """
        self.transport = LossyTransport(self.transport, self.lossPr)
        DatagramProtocol.transport = self.transport

    def datagramReceived(self, datagram, host_port):
        """
        :param string datagram: the payload of the UDP packet.
        :param host_port: a touple containing the source IP address and port.
        
        Twisted calls this method when the server has received a UDP
        packet.  You cannot change the signature of this method.
        """
        Packet=struct.unpack('>BBHHH'+str(len(datagram)-8)+'s',datagram) 
        Version=Packet[0]//(2**4)
        Type=Packet[0]-(2**4)*(Packet[0]//(2**4))
        SessionToken=Packet[1]*(2**16)+Packet[2]
        self.SequenceNumber=Packet[3]
        PayloadSize=Packet[4]
        Payload=Packet[5]

        #if Type==0:
          #self.tokenSequenceNumber.remove(SessionToken,SequenceNumber)
        #if SequenceNumber and SessionToken not in self.SequenceTokenList: 

        if Type!=0:## if the datagram isn't an ACK we have to send one to the client
            
            Ack=struct.pack('>BBHHH',16,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),self.SequenceNumber,0)
            self.transport.write(Ack,host_port)

        if Type==1 :

            uData=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            uName=struct.unpack('H'+str(len(uData[1])-2)+'s',uData[1])
            userName=uName[1].decode('utf-8') 
         
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
                userID=1
                #while not(self.serverProxy.getUserById(userID)):
                #userID+=1

                uData=struct.pack('>H'+str(len(uData[1]))+'s',userID,uData[1])
            Version=1
            Type=2
            Payload=struct.pack('>B'+str(len(uData))+'s',ResponseCode,uData)
            LoginResponse=struct.pack('>BBHHH'+str(len(Payload))+'s',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),self.SequenceNumber,len(Payload),Payload)
            self.transport.write(LoginResponse,host_port)
            #self.tokenSequenceList.append(SessionToken)
            #self.tokenSequenceList.append(SequenceNumber)
            #Packet=struct.unpack('>BBHHH'+str(len(datagram)-8)+'s',datagram)
            #Version=Packet[0]//2**4
            #Type=Packet[0]-Packet[0]//2**4
            #SessionToken=Packet[1]*(2**16)+Packet[2]
            #SequenceNumber=Packet[3]
            #PayloadSize=Packet[4]
            #Payload=Packet[5]
            
                

      #        def RST(self,Rname):
       #         if Rname='Main Room':
       #             RoomID=1
       #             MovieIP=0
       #             MoviePort=0
       #             MovieL=self.serverProxy.getMovieList()
       #         else:
       #             RoomID=self.serverProxy.getMovieByTitle(Rname).movieID
       #             MovieIP=self.serverProxy.getMovieAddressPort(Rname)[0]
       #             MoviePort=self.serverProxy.getMovieAddressPort(Rname)[1]           
       #             MovieL=[]
       #        RoomName=struct.pack('H'+str(len(Rname))+'s',len(Rname),Rname.encode('utf-8')
       #       
      #         for User in self.server.getUserList() :
       #            if User.userChatRoom=='Rname'
        #               UsersList.append(struct.pack('>HH'+str(len(User))+'s',User.userid,len(User.username),userName.encode('utf-8'))
        #       Userlist.append(struct.pack('>'+str(len(User)+'s',User)"""
                    
                       

               
        
        
            #self.serverProxy.addUser(userName,'Main Room',None,host_port)
            #SequenceNumber+=1
            #RoomIdentifier=1 
            #RoomName=struct.pack('>H9s',9,'Main Room'.encode('utf-8'))
            #MovieIP=0
            #MoviePort=0
            #UsersMainRoom=[]
            #for user in self.serverProxy.getUserList():
                #if user.userChatRoom=='Main Room':
                        #UsersMainRoom.append(struct.pack('>HH'+str(len(user.userName))+'s',user.userId,len(user.userName),userName.encode('utf-8')))
          #NumberOfFilms=len(self.serverProxy.getUserList())
          #for Movie in self.serverProxy.getUserList():
              #RoomId=self.serverProxy.getMovieAddrPort(Movie)
              #RoomName=self.serverProxy.
         #length UsersMainRoom
#Room List : number of films available , pour chaque film Room Identifier , Room Name , MovieIP , MoviePort


                 
            
            
        pass
