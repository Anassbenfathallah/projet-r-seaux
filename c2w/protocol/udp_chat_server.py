# -*- coding: utf-8 -*-
from twisted.internet.protocol import DatagramProtocol
from c2w.main.lossy_transport import LossyTransport
import logging
import struct
import random
from twisted.internet import reactor
from twisted.internet import task

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
        self.TokenHaveToWait=[]
        self.UsNamSesTokSeqNbHP=[]
        self.StillAlive=[]


    def startProtocol(self):
        """
        DO NOT MODIFY THE FIRST TWO LINES OF THIS METHOD!!

        If in doubt, do not add anything to this method.  Just ignore it.
        It is used to randomly drop outgoing packets if the -l
        command line option is used.
        """
        self.transport = LossyTransport(self.transport, self.lossPr)
        DatagramProtocol.transport = self.transport


    def SendHelloMessage(self,host_port,n):

        for i in self.StillAlive:
            if (i[0],i[1])==(host_port,n):
                Version=1
                Type=8
                for User in self.UsNamSesTokSeqNbHP:
                    if User[3]==host_port:
                        SessionToken=User[1]
                        UserName=User[0]
                        if User[2]==65535:
                            User[2]=-1                    
                        SequenceNumber=User[2]+1
                        User[2]+=1
                PayloadSize=0
                HEL=struct.pack('>BBHHH',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize)
                self.transport.write(HEL,host_port)
                reactor.callLater(10,self.SendHelloMessage,host_port,n)
                self.TokenHaveToWait.append([host_port,SessionToken,SequenceNumber,8,UserName,1])
                reactor.callLater(1,self.Reemission,HEL,host_port,SessionToken,SequenceNumber)
            


    def Reemission(self,Message,host_port,SessionToken,SequenceNumber):
        
        for user in self.UsNamSesTokSeqNbHP:
            if (user[1],user[3])==(SessionToken,host_port):
                UserName=user[0]
        if self.serverProxy.getUserByName(UserName)!=None:

            for i in self.TokenHaveToWait:
                if (host_port,SessionToken,SequenceNumber)==(i[0],i[1],i[2]):
                    if i[5]>3:
                        self.serverProxy.removeUser(i[4])
                        self.TokenHaveToWait.remove(i)
                        for user in self.UsNamSesTokSeqNbHP:
                            if (user[1],user[3])==(SessionToken,host_port):
                                self.UsNamSesTokSeqNbHP.remove(user) 
                    else:              
                        self.transport.write(Message,host_port)
                        i[5]+=1
                        reactor.callLater(1,self.Reemission,Message,host_port,SessionToken,SequenceNumber)
                
        

    def RST(self,RoomN):
        RoomList=bytearray(0)
        if RoomN=='Main Room':
            RoomIdentifier=1
            MovieIP=0
            MoviePort=0
            MovieList=self.serverProxy.getMovieList()
        else:                
            RoomIdentifier= self.serverProxy.getMovieByTitle(RoomN).movieId
            MovieIP= self.serverProxy.getMovieAddrPort(RoomN)[0].split(".")
            MovieIP=int(MovieIP[0])*2**24+int(MovieIP[1])*2**16+int(MovieIP[2])*2**8+int(MovieIP[3])
            MoviePort=self.serverProxy.getMovieAddrPort(RoomN)[1]
            MovieList=[]
        RoomName=struct.pack('>H'+str(len(RoomN))+'s',len(RoomN),RoomN.encode('utf-8'))      
        Users=[]
        for User in self.serverProxy.getUserList():
            if User.userChatRoom==RoomN:
                Users.append(struct.pack('>HH'+str(len(User.userName))+'s',User.userId,len(User.userName),User.userName.encode('utf-8')))
        UserList=bytearray(0)
        UserList.extend(struct.pack('>H',len(Users)))
        for User in Users:
            UserList.extend(struct.pack('>'+str(len(User))+'s',User))        
        RoomList.extend(struct.pack('>H',len(MovieList)))
        for Movie in MovieList:
            MovieIPsplit=self.serverProxy.getMovieAddrPort(Movie.movieTitle)[0].split(".")
            MovieIPbin=int(MovieIPsplit[0])*2**24+int(MovieIPsplit[1])*2**16+int(MovieIPsplit[2])*2**8+int(MovieIPsplit[3])
            RoomList.extend(struct.pack('>HH'+str(len(Movie.movieTitle))+'sIH',Movie.movieId,len(Movie.movieTitle),Movie.movieTitle.encode('utf-8'),MovieIPbin,self.serverProxy.getMovieAddrPort(Movie.movieTitle)[1]))
            Users=[]
            for User in self.serverProxy.getUserList():
                if User.userChatRoom==Movie.movieTitle:
                    Users.append(struct.pack('>HH'+str(len(User.userName))+'s',User.userId,len(User.userName),User.userName.encode('utf-8')))
            UserListMovie=bytearray(0)
            UserListMovie.extend(struct.pack('>H',len(Users)))
            for User in Users:
                UserListMovie.extend(struct.pack('>'+str(len(User))+'s',User))
            RoomList.extend(struct.pack('>'+str(len(UserListMovie))+'sH',UserListMovie,0))
        Payload=struct.pack('>H'+str(len(RoomName))+'sIH'+str(len(UserList))+'s'+str(len(RoomList))+'s',RoomIdentifier,RoomName,MovieIP,MoviePort,UserList,RoomList)
        PayloadSize=len(Payload)
        for User in self.serverProxy.getUserList(): 
            if User.userChatRoom==RoomN:
                for i in self.UsNamSesTokSeqNbHP:
                    if i[0]==User.userName:
                        SessionToken=i[1]
                        if i[2]==65535:
                            i[2]=-1                    
                        SequenceNumber=i[2]+1
                        i[2]+=1
                RST=struct.pack('>BBHHH'+str(PayloadSize)+'s',20,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize,Payload)
                self.transport.write(RST,User.userAddress)
                self.TokenHaveToWait.append([User.userAddress,SessionToken,SequenceNumber,0,None,1]) #(Address,ST,SN,Type,UserName,Iter)
               
                        

                ########Prepare Reemission#####################################################################################
                
                reactor.callLater(1,self.Reemission,RST,User.userAddress,SessionToken,SequenceNumber) 



    def datagramReceived(self, datagram, host_port):
        """
        :param string datagram: the payload of the UDP packet.
        :param host_port: a touple containing the source IP address and port.
        
        Twisted calls this method when the server has received a UDP
        packet.  You cannot change the signature of this method.
        """
        ##############Reception#####################################################################################################

        Data=struct.unpack('>BBHHH'+str(len(datagram)-8)+'s',datagram)
        Version,Type,SessionToken,SequenceNumber,PayloadSize,Payload=Data[0]//(2**4),Data[0]-(2**4)*(Data[0]//(2**4)),Data[1]*2**16+Data[2],Data[3],Data[4],Data[5]
                
        ##############Acknowledgement###############################################################################################


        if Type!=0:
            
            ACK=struct.pack('>BBHHH',16,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,0)
            self.transport.write(ACK,host_port)
            
            ########prepare the keepalive##############################################################################################

            for i in self.StillAlive:
                if i[0]==host_port:
                    i[1]+=1            
                    reactor.callLater(10,self.SendHelloMessage,host_port,i[1])
           
        ##############WaitForAnACK and RST after a LRP##################################################################################################

        if Type==0:
            
            ##########Remove Message from Waitlist###############################################################################

            for i in self.TokenHaveToWait:
                if (i[0],i[1],i[2])==(host_port,SessionToken,SequenceNumber):
                    Type=i[3]
                    userName=i[4]
                    self.TokenHaveToWait.remove([host_port,SessionToken,SequenceNumber,Type,userName,1])
                    
       
        ##############LRP########################################################################################################### 
 
        if Type==1 and SessionToken==0 and SequenceNumber==0 and PayloadSize==len(Payload):
            
            UserData=struct.unpack('>H'+str(len(Payload)-2)+'s',Payload)
            UserName=struct.unpack('>H'+str(len(UserData[1])-2)+'s',UserData[1])
            userName=UserName[1].decode('utf-8')           
           
            if self.serverProxy.userExists(userName)==True:
                ResponseCode=3
                UserData=struct.pack('>H'+str(len(UserData[1]))+'s',0,UserData[1])
            
            elif len(userName)>100:
                ResponseCode=2
                UserData=struct.pack('>H'+str(len(UserData[1]))+'s',0,UserData[1])
   
            elif len(self.serverProxy.getUserList())>65535:
                ResponseCode=4
                UserData=struct.pack('H'+str(len(UserData[1]))+'s',0,UserData[1])
            
            else:
                UserId=self.serverProxy.addUser(userName,'Main Room',None,host_port)
                UserData=struct.pack('>H'+str(len(UserData[1]))+'s',UserId,UserData[1])
                ResponseCode=0
                SessionToken=random.getrandbits(24)
                self.UsNamSesTokSeqNbHP.append([userName,SessionToken,SequenceNumber,host_port])
                self.TokenHaveToWait.append([host_port,SessionToken,SequenceNumber,4,userName,1])
                self.StillAlive.append([host_port,0])
                reactor.callLater(10,self.SendHelloMessage,host_port,0)

            Type=2
            Payload=struct.pack('>B'+str(len(UserData))+'s',ResponseCode,UserData)
            PayloadSize=len(Payload)           
            LRP=struct.pack('>BBHHH'+str(PayloadSize)+'s',Version*2**4+Type,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize,Payload)
            self.transport.write(LRP,host_port)
   
            ##########Prepare reemission in case of non-ACK###########################################################################

            reactor.callLater(1,self.Reemission,LRP,host_port,SessionToken,SequenceNumber)
                
        #########Send RST to all clients in Main Room####################################################################################################

        if Type==4:
            
            self.RST('Main Room')


        #############GTR traitement##################################################################################################       
            
        if Type==5:

            RoomID=struct.unpack('>H',Payload)[0] 
            RoomName=self.serverProxy.getMovieById(RoomID)
            if RoomName==None:
                RoomName='Main Room'
            else:
                RoomName=self.serverProxy.getMovieById(RoomID).movieTitle
            for User in self.UsNamSesTokSeqNbHP:
                if User[1]==SessionToken:
                    UserName=User[0]
            PreviousRoom=self.serverProxy.getUserByName(UserName).userChatRoom  
            self.serverProxy.updateUserChatroom(UserName,RoomName)
            if RoomName=='Main Room':
                self.serverProxy.stopStreamingMovie(PreviousRoom)
            else:
                self.serverProxy.startStreamingMovie(RoomName)
            self.RST(PreviousRoom)
            self.RST(RoomName)
            
        #############MSG traitement ans send to other users###################################################################################################

        if Type==6:
            
            (UserId,MessageSize,Message)=struct.unpack('>HH'+str(PayloadSize-4)+'s',Payload)
            User=self.serverProxy.getUserById(UserId)
            for user in self.serverProxy.getUserList():
                if user.userChatRoom==User.userChatRoom and user.userName!=User.userName:
                    for i in self.UsNamSesTokSeqNbHP:
                        if i[0]==user.userName:
                            SessionToken=i[1]
                            if i[2]==65535:
                                i[2]=-1                    
                            SequenceNumber=i[2]+1
                            i[2]+=1
                    MSG=struct.pack('>BBHHH'+str(PayloadSize)+'s',22,SessionToken//(2**16),SessionToken-(2**16)*(SessionToken//(2**16)),SequenceNumber,PayloadSize,Payload)
                    self.transport.write(MSG,user.userAddress)
                    self.TokenHaveToWait.append([user.userAddress,SessionToken,SequenceNumber,0,None,1])
            
                    ########Prepare Reemission#####################################################################################
                
                    reactor.callLater(1,self.Reemission,MSG,user.userAddress,SessionToken,SequenceNumber)          
            
        
        #################LOR traitement###################################################################################################################

        if Type==7:

            for User in self.UsNamSesTokSeqNbHP:
                if User[1]==SessionToken:
                    UserName=User[0]
            self.serverProxy.removeUser(UserName)
            self.RST('Main Room')
            
            


        pass
