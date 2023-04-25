from concurrent import futures
from time import sleep

import grpc

import banking_pb2_grpc
from banking_pb2 import MsgRequest, MsgResponse


class Branch(banking_pb2_grpc.BankServicer):
    def __init__(self, id, balance, branches):
        # unique ID of the Branch
        self.id = id
        # replica of the Branch's balance
        self.balance = balance
        # the list of process IDs of the branches
        self.branches = branches
        # the list of Client stubs to communicate with the branches
        self.stubList = list()
        # a list of received messages used for debugging purpose
        self.recvMsg = list()
        # iterate the processID of the branches

         # TODO: students are expected to store the processID of the branches
        # pass

    # TODO: students are expected to process requests from both Client and Branch
    def createServer(self):

        #configure grpc server for each branch 
        port = "localhost:" + str(50000 + self.id)
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=6))
        banking_pb2_grpc.add_BankServicer_to_server(self, server)
        server.add_insecure_port(port)
        server.start()

        #create stubList
        for branchId in self.branches:
            if branchId != self.id:
                port = "localhost:" + str(50000 + branchId)
                self.stubList.append(banking_pb2_grpc.BankStub(grpc.insecure_channel(port)))
        
        #keep server opening to wait all transactions finsih
        sleep(900)
        server.stop()

    def MsgDelivery(self, request, context):
        message = "success"
        
        #main function to implement query, deposit and withdraw task
        if request.interface == "query":
            return MsgResponse(interface=request.interface, result=message, money=self.balance)
        elif request.interface == "deposit":
            self.balance += request.money
            # use type "Customer" to identify Customer request
            if request.type == "customer":
                self.MsgPropagate(request)
        elif request.interface == "withdraw":
            if self.balance >= request.money:
                self.balance -= request.money
                if request.type == "customer":
                    self.MsgPropagate(request)
            else:
                message = "no enough money"

        return MsgResponse(interface=request.interface, result=message, money=self.balance)

    # only use for propagating between in branches, use type "branch" to identify Branch request
    def MsgPropagate(self, request):
        for stub in self.stubList:
            stub.MsgDelivery(MsgRequest(id=request.id, interface=request.interface, money=request.money, type = "branch"))
