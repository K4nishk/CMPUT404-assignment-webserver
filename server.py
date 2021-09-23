#  coding: utf-8 
import socketserver, os
from urllib.parse import unquote

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/


class MyWebServer(socketserver.BaseRequestHandler):

    def buildResponse(self, protocol, status, filepath):
        """
        FUNCTIONALITY:
            * This method is being used to create appropriate responses based on the status of the requested address.

        ARGUMENTS:
            * self: The instance of the class.
            * protocol: The protocol that is being used by the client to establish the connection.
            * status: The status code/message that was generated based on the address's access.
            * filepath: It is the path to the file requested from the root directory.

        RETURNS:
            * response: A string which contains the HTTP Header data and the HTML document.
        """

        response = ""
        if status.split()[0] == "200":
            content, contentLength = self.getContent(filepath)

            # Resolved the case of connection staying intact after the code response was sent using Martin's explanation.
            # https://stackoverflow.com/questions/61880928/what-does-connection-0-to-host-example-com-left-intact-mean
            response = protocol + " " + status + self.getContentType(filepath) + contentLength + "Connection: closed\r\n\r\n" + content
        elif status.split()[0] == "301":
            content, contentLength = self.getContent(filepath)
            response = protocol + " " + status + self.getContentType(filepath) + contentLength + "Connection: closed\r\n\r\n" + content
        else:
            error, errorLength = self.buildErrorPage(status)
            response = protocol + " " + status + errorLength + "Content-Type: text/html; charset=UTF-8\r\n" + "Connection: closed\r\n\r\n" + error

        return response


    def buildErrorPage(self, status):
        """
        FUNCTIONALITY:
            * This method is creates a separate HTML page for the error responses that need to be returned such as 404.

        ARGUMENTS:
            * self: The instance of the class.
            * status: The status code/message that was generated based on the address's access.

        RETURNS:
            * errorInHtml: A string which contains the HTML document.
            * errorLength: A string converted int which contains the length of the data inside the HTML page, i.e. errorInHtml
        """

        htmlHeader = "<!DOCTYPE html>\n<head><meta charset='UTF-8'></head>\n<html>\n<body>\n"
        htmlFooter = "</body>\n</html>"

        errorInHtml = htmlHeader + status + htmlFooter            
        errorLength = "Content-Length: " + str(len(errorInHtml)) + "\r\n"

        return errorInHtml, str(errorLength)


    def getContentType(self, filepath):
        """
        FUNCTIONALITY:
            * This method is used to get the MIME-TYPE of the file requested.

        ARGUMENTS:
            * self: The instance of the class.
            * filepath: It is the path to the file requested from the root directory.

        RETURNS:
            * contentType: A string that returns the file type along with the appended HTTP header info and CLRF. 
        """

        contentType = "Content-type: "
        if "." not in filepath:
            contentType = contentType + "application/octet-stream"
            # contentType = contentType + "text/plain; charset=UTF-8"
        
        else:
            if filepath[filepath.find(".") + 1 :] == "html":
                contentType = contentType + "text/html; charset=UTF-8"
            elif filepath[filepath.find(".") + 1 :] == "css":
                contentType = contentType + "text/css; charset=UTF-8"
        
        return contentType + "\r\n"


    def getContent(self, filepath):
        """
        FUNCTIONALITY:
            * This method is used to get the data of the file requested.

        ARGUMENTS:
            * self: The instance of the class.
            * filepath: It is the path to the file requested from the root directory.

        RETURNS:
            * content: A string that contains the data from the read file with appended CRLF.
            * contentLength: A string converted int that contains the length of the data inside the requested file. 
        """

        content = ""
        contentLength = "Content-Length: "
        try:
            file = open(filepath, "r")
            data = file.read()
            if data != "":
                content = "\r\n" + data
        except:
            print("Couldn't open file")
            return -1, -1

        file.close()

        # minus 2 because I append \r\n to the content string.
        contentLength = contentLength + str(len(content) - 2) + "\r\n"
        
        return content, contentLength


    def handle(self):
        """
        FUNCTIONALITY:
            * This method must do all the work required to service a request.
            https://docs.python.org/3/library/socketserver.html#socketserver.BaseRequestHandler

        ARGUMENTS:
            * self: The instance of the class.

        RETURNS:
            * None
        """

        self.data = self.request.recv(1024).strip()
        print ("Got a request of: %s\n" % self.data)

        print("=====")
        # Extract the GET request
        request = unquote(self.data.decode()).split("\r\n")[0]

        method = request[:request.find(" /")]       # HTTP method
        protocol = request[request.find("HTTP"):]   # the protocol
        filepath = request.replace(method, "").replace(protocol,"").strip(" ")  # remove extras to get the requested path
        
        # If there is /../ in the GET request, we don't allow it.
        cFlag = True
        if (filepath + "/").find("/../"):
            cFlag = False 

        # Allowing only ./www directory
        filepath = "www" + filepath

        status = ""
        if method != "GET":
            # The request method is not GET so, return 405. 
            status = "405 Method Not Allowed\r\n"
        else:
            # os.path methods referenced from:
            # https://www.guru99.com/python-check-if-file-exists.html
            if cFlag:
                # Trying to access other directories. Return 404 status code.
                status = "404 Not Found\r\n"
            else:
                if os.path.isdir(filepath):
                    # It is a directory.

                    if filepath[-1] == "/":
                        # If the last character of the filepath is "/", then we simply display the index.html in the directory
                        filepath = filepath + "index.html"
                        if not (os.path.exists(filepath)):
                            # If the directory is empty and thereby no index.html file is present. Return 404.
                            status = "404 Not Found\r\n"
                        else:
                            # Else the file is found and we send the data.
                            status = "200 OK\r\n"
                    else:
                        # Otherwise, we have to correct the path by appending a "/" and return a 301 code and do the same jazz as before.
                        filepath = filepath + "/index.html"
                        if not (os.path.exists(filepath)):
                            # If the directory is empty and thereby no index.html file is present. Return 404.
                            status = "404 Not Found\r\n"
                        else:
                            # Else the file is found and we send the data with 301 code.
                            status = "301 Moved Permanently\r\n"

                            # Send the response right now and make status an empty string so that the response isn't sent again
                            response = self.buildResponse(protocol, status, filepath)
                            self.request.sendall(bytearray(response, "utf-8"))
                            status = ""                     

                else:
                    # It is a file
                    if not (os.path.exists(filepath)):
                        # If the file requested doesn't exist in the root directory.
                        status = "404 Not Found\r\n"
                    else:
                        if os.path.isfile(filepath):
                            # Confirmt that the file indeed is a file
                            status = "200 OK\r\n"
                        else:
                            # at this point there should be no cases left to handle but for safety reasons, return 404
                            status = "404 Not Found\r\n"

        if status != "":
            response = self.buildResponse(protocol, status, filepath) 
            self.request.sendall(bytearray(response, "utf-8"))
            print("-----")


if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
