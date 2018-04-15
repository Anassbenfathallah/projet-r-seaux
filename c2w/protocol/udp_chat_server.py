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
        self.tokenList=[]

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
        Version=Packet[0]//16
        Type=Packet[0]-16*(Packet[0]//(16))
        Token=Packet[1]*(2**16)+Packet[2]
        Number=Packet[3]
        PSize=Packet[4]
        Payload=Packet[5]

       def RST(self,Rname):
              RoomName=struct.pack('H'+str(len(Rname))+'s',len(Rname),Rname.encode('utf-8'))
              UsersList=[]
              if Rname=='Main Room':# si la  salle en question est la main room on connaît déja son ID , son IP et Port
                  RoomID=1
                  MovieIP=0
                  MoviePort=0
                  MovieL=self.serverProxy.getMovieList()
              else:# sinon on les trouve grâce aux méthodes du serverProxy
                  RoomID=self.serverProxy.getMovieByTitle(Rname).movieID
                  MovieIP=self.serverProxy.getMovieAddressPort(Rname)[0]
                  MoviePort=self.serverProxy.getMovieAddressPort(Rname)[1]           
                  MovieL=[]#la liste des films est vide si on ne se trouve pas dans la mainroom
              for User in self.serverProxy.getUserList() :
                  if User.userChatRoom=='Rname':
                      UsersList.append(struct.pack('>HH'+str(len(User))+'s',User.userid,len(User.username),userName.encode('utf-8')))
              UsersListSize=len(UsersList)
              UsersList=struct.pack('>H',UsersListsize).extend(UsersList)
              RoomList=[]
              RoomList.append(len(MovieL))
              return([RoomID,RoomNameMovieIP,MoviePort,MovieL,UsersList,RoomList])
              for Movie in MovieL : 
                  RoomList.extend(RST(self,Movie))#structure récursive
              Payload=struct.pack('>H'+str(len(RoomName))+'sIH'+str(len(UserList))+'s'+str(len(RoomList))+'s',RoomID,RoomName,MovieIP,MoviePort,UsersList,RoomList)
              PSize=len(Payload)
              RST=struct.pack('>BBHHH'+str(PSize)+'s',20,Token//(2**16),Token-(2**16)*(Token//(2**16)),Number,PSize,Payload)
              self.transport.write(RST,User.userAddress)
                   
        
        if Type!=0:## if the datagram isn't an ACK we have to send one to the client
            
            Ack=struct.pack('>BBHHH',16,Token//(2**16),Token-(2**16)*(Token//(2**16)),Number,0)
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
                Token=random.getrandbits(24)
            Version=1
            Type=2
            Payload=struct.pack('>B'+str(len(uData))+'s',ResponseCode,uData)
            LoginResponse=struct.pack('>BBHHH'+str(len(Payload))+'s',Version*2**4+Type,Token//(2**16),Token-(2**16)*(Token//(2**16)),Number,len(Payload),Payload)
            self.transport.write(LoginResponse,host_port)
   
        if Type==4:
            
            self.RST('Main Room')
         
           
            def RST(self,Rname):
                RoomName=struct.pack('H'+str(len(Rname))+'s',len(Rname),Rname.encode('utf-8'))
                UsersList=[]
                if Rname=='Main Room':# si la  salle en question est la main room on connaît déja son ID , son IP et Port
                    RoomID=1
                    MovieIP=0
                    MoviePort=0
                    MovieL=self.serverProxy.getMovieList()
                else:# sinon on les trouve grâce aux méthodes du serverProxy
                    RoomID=self.serverProxy.getMovieByTitle(Rname).movieID
                    MovieIP=self.serverProxy.getMovieAddressPort(Rname)[0]
                    MoviePort=self.serverProxy.getMovieAddressPort(Rname)[1]           
                    MovieL=[]#la liste des films est vide si on ne se trouve pas dans la mainroom
                for User in self.serverProxy.getUserList() :
                    if User.userChatRoom=='Rname':
                        UsersList.append(struct.pack('>HH'+str(len(User))+'s',User.userid,len(User.username),userName.encode('utf-8')))
                UsersListSize=len(UsersList)
                UsersList=struct.pack('>H',UsersListsize).extend(UsersList)
                RoomList=[]
                RoomList.append(len(MovieL))
                return([RoomID,RoomNameMovieIP,MoviePort,MovieL,UsersList,RoomList])
                for Movie in MovieL : 
                    RoomList.extend(RST(self,Movie))#structure récursive
                Payload=struct.pack('>H'+str(len(RoomName))+'sIH'+str(len(UserList))+'s'+str(len(RoomList))+'s',RoomID,RoomName,MovieIP,MoviePort,UsersList,RoomList)
                PSize=len(Payload)
                RST=struct.pack('>BBHHH'+str(PSize)+'s',20,Token//(2**16),Token-(2**16)*(Token//(2**16)),Number,PSize,Payload)
                self.transport.write(RST,User.userAddress)
                   
                    
    
        if Type==5:
            RoomID=struct.unpack('>H',Payload)[0]
            RoomName=self.serverProxy.getMovieById(RoomID)
            if MovieName==None:
                RoomName='Main Room'
            else : 
                RoomName=self.serverProxy.getMovieById(RoomId).movieTitle

       if Type==7:
           # on trouve le username qui a pour session Token celui envoyé deans le LOR
           self.serverProxy.removeUser(UserName)
                
            
                                    
        
           

                 
            
            
        pass
