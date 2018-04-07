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

        self.UserId=0
        self.SessionToken=0

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
        SequenceNumber=0
        usName=userName.encode('utf-8')
        uName=struct.pack('>H'+str(len(usName))+'s',len(usName),usName)
        Payload=struct.pack('>H'+str(len(uName))+'s',0,uName)
        Psize=len(Payload)
        LoginRequest=struct.pack('>BBHHH'+str(Psize)+'s',Version*2**4+Type,self.SessionToken//(2**16),self.SessionToken-(2**16)*self.SessionToken//(2**16),SequenceNumber,Psize,Payload)
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
        pass

    def sendLeaveSystemRequestOIE(self):
        """
        Called by the client proxy  when the user
        has clicked on the leave button in the main room.
        """
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
        SequenceNumber=Packet[3]
        PayloadSize=Packet[4]
        Payload=Packet[5]

   
        if Type!=0:## if the datagram isn't an ACK we have to send one to the client
            
            Ack=struct.pack('>BBHHH',16,self.SessionToken//(2**16),self.SessionToken-(2**16)*(self.SessionToken//(2**16)),SequenceNumber,0)
            self.transport.write(Ack,host_port)


        pass
