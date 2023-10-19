#!/usr/bin/env python3
#
# Bank Server application
# Jimmy da Geek

import sys
import socket
import selectors
import types


HOST = "127.0.0.1"      # Standard loopback interface address (localhost)
PORT = 65432            # Port to listen on (non-privileged ports are > 1023)
ALL_ACCOUNTS = dict()   # keys are account numbers, value are BankAccount instances
ACTIVE_ACCOUNTS = dict() # keys are account numbers, values are the IP addresses of the clients currently accessing the account
ACCT_FILE = "accounts.txt"

##########################################################
#                                                        #
# Bank Server Core Functions                             #
#                                                        #
# No Changes Needed in This Section                      #
#                                                        #
##########################################################

def acctNumberIsValid(ac_num):
    """Return True if ac_num represents a valid account number. This does NOT test whether the account actually exists, only
    whether the value of ac_num is properly formatted to be used as an account number.  A valid account number must be a string,
    lenth = 8, and match the format AA-NNNNN where AA are two alphabetic characters and NNNNN are five numeric characters."""
    return isinstance(ac_num, str) and \
        len(ac_num) == 8 and \
        ac_num[2] == '-' and \
        ac_num[:2].isalpha() and \
        ac_num[3:8].isdigit()

def acctPinIsValid(pin):
    """Return True if pin represents a valid PIN number. A valid PIN number is a four-character string of only numeric characters."""
    return (isinstance(pin, str) and \
        len(pin) == 4 and \
        pin.isdigit())

def amountIsValid(amount):
    """Return True if amount represents a valid amount for banking transactions. For an amount to be valid it must be: \n
    (A) coercable to a float\n
    (B) a positive value with at most two decimal places."""
    try:
        amount = float(amount)
    except ValueError: 
        return False
    return (round(amount, 2) == amount) and (amount >= 0)

def as_numeric(amount):
    '''If the amount is numeric (can be converted to float using Python's float() method),
    return as float. Otherwise, return None.'''
    try:
       return float(amount)
    except ValueError:
        return None

class BankAccount:
    """BankAccount instances are used to encapsulate various details about individual bank accounts."""
    acct_number = ''        # a unique account number
    acct_pin = ''           # a four-digit PIN code represented as a string
    acct_balance = 0.0      # a float value of no more than two decimal places
    
    def __init__(self, ac_num = "zz-00000", ac_pin = "0000", bal = 0.0):
        """ Initialize the state variables of a new BankAccount instance. """
        if acctNumberIsValid(ac_num):
            self.acct_number = ac_num
        if acctPinIsValid(ac_pin):
            self.acct_pin = ac_pin
        if amountIsValid(bal):
            self.acct_balance = bal

    def deposit(self, amount):
        """ Make a deposit. The value of amount must be valid for bank transactions. If amount is valid, update the acct_balance.
        Returns success_code.
        Success codes are: 0: valid result; 1: invalid amount given. """
        result_code = 0
        if not amountIsValid(amount):
            result_code = 1
        else:
            # valid amount, so add it to balance and set succes_code 1
            self.acct_balance = round(self.acct_balance + amount, 2)
        return result_code

    def withdraw(self, amount):
        """ Make a withdrawal. The value of amount must be valid for bank transactions. If amount is valid, update the acct_balance.
        Returns success_code.
        Success codes are: 0: valid result; 1: invalid amount given; 2: attempted overdraft. """
        result_code = 0
        if not amountIsValid(amount):
            # invalid amount, return error 
            result_code = 1
        elif amount > self.acct_balance:
            # attempted overdraft
            result_code = 2
        else:
            # all checks out, subtract amount from the balance
            self.acct_balance = round(self.acct_balance - amount, 2)
        return result_code

def get_acct(acct_num):
    """ Lookup acct_num in the ALL_ACCOUNTS database and return the account object if it's found.
        Return False if the acct_num is invalid. """
    if acctNumberIsValid(acct_num) and (acct_num in ALL_ACCOUNTS):
        return ALL_ACCOUNTS[acct_num]
    else:
        return False

def load_account(num_str, pin_str, bal_str):
    """ Load a presumably new account into the in-memory database. All supplied arguments are expected to be strings. 
        num_str is the account ID"""
    try:
        # it is possible that bal_str does not represent a float, so be sure to catch that error.
        bal = float(bal_str)
    except ValueError:
        print(f"error loading acct '{num_str}': balance value not a float")
        return False
    if acctNumberIsValid(num_str):
        if get_acct(num_str):
            print(f"Duplicate account detected: {num_str} - ignored")
            return False
        # We have a valid new account number not previously loaded
        new_acct = BankAccount(num_str, pin_str, bal)
        # Add the new account instance to the in-memory database
        ALL_ACCOUNTS[num_str] = new_acct
        print(f"loaded account '{num_str}'")
        return True
    return False
    
    
def load_all_accounts(acct_file = "accounts.txt"):
    """ Load all accounts into the in-memory database, reading from a file in the same directory as the server application. """
    print(f"loading account data from file: {acct_file}")
    with open(acct_file, "r") as f:
        while True:
            line = f.readline()
            if not line:
                # we're done
                break
            if line[0] == "#":
                # comment line, no error, ignore
                continue
            # convert all alpha characters to lowercase and remove whitespace, then split on comma
            acct_data = line.lower().replace(" ", "").split(',')
            if len(acct_data) != 3:
                print(f"ERROR: invalid entry in account file: '{line}' - IGNORED")
                continue
            load_account(acct_data[0], acct_data[1], acct_data[2])
    print("finished loading account data")
    return True

def save_all_accounts(acct_file = "accounts.txt"):
    ''' Save all accounts stored in runtime database, writing to acct_file.'''
    print(f"storing account data to file: {acct_file}")
    with open(acct_file, "w") as f:
        for acct in ALL_ACCOUNTS.values: # Overwrites any comments
            f.write(f"{acct.acct_number}, {acct.acct_pin}, {acct.acct_balance}")
            
##########################################################
#                                                        #
# Bank Server Network Operations                         #
#                                                        #
# Much of this code came from https://realpython.com/python-sockets/
#                                                        #
##########################################################

def run_network_server(): # CHANGE docstring
    """ Uses a selector from the selectors module to switch between accepting new client connections and servicing existing ones.
    Sets up the server's listening socket at addresss (HOST, PORT). Runs until a KeyBoardInterupt closes the server. All runtime changes to 
    accounts are saved at this point, in the file ACCT_FILE."""
    # Allows the server to address all client connections (and new connection requests) in a 
    # popcorn-conversation style. We register sockets with the selector. Whenever its select() method is called, 
    # it returns the ones that are ready to deliver or receive data. One socket for evey active client session,
    # plus one to listen for new connections on.
    sel = selectors.DefaultSelector()
    lsock = listening_sock(sel)
    try:
        while True:
            # Returns all the sockets that are ready to be serviced.
            # the event(s) indicating the socket is available for read or write occurred.
            events = sel.select(timeout=None) # timeout=None - Blocks until there are sockets ready.
            # key is a namedtuple holding the socket object and associated data
            # mask holds information on the I/O events
            for key, mask in events:
                # We associate data with all the sockets representing client connections.
                # If there is no data, this must be the server's listening socket.
                if key.data is None: 
                    accept_connection(lsock=key.fileobj, sel=sel)
                else:
                    # key represents a client connection, mask indicates whether it's ready for read or write, inclusive.
                    service_connection(key, mask, sel)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt. ", end="")
    finally:
        print("Saving and exiting.")
        save_all_accounts(ACCT_FILE) 
        lsock.close()
        sel.close()
    return

def listening_sock(selector, addr=(HOST, PORT)) -> socket.socket:
    '''Create the server's listening socket, registers it with the selector to 
    monitor for READ availibility events.\n

    addr is a known IP address and port number for the listening socket so 
    clients know where to find it. '''
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind(addr)
    lsock.listen()
    print(f"Listening on {addr}")
    lsock.setblocking(False) # so the server can do other things while it waits for new connections.
    selector.register(lsock, selectors.EVENT_READ, data=None)
    return lsock

def accept_connection(lsock, sel) -> type[socket.socket]:
    '''Accepts the connection made to listening socket lsock, registers the new socket 
    representing that client connection with selector to monitor for READ or WRITE availibility.

    Associates the new connection with some data: \n
    \t inb - data that we are in the process of receiving \n
    \t outb - data we wish to send \n
    \t auth - account number identifying which account (if any) the client is authorized to access

    '''
    conn, addr = lsock.accept()  # Should be ready to read
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    # Associates data with the new client connection:
    #   inb  = data that we are in the process of receiving
    #   outb = data we wish to send 
    #   addr = client address, already stored by socket object but this allows easier access
    #   auth = account number, identifying an account the client is authorized to access
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", auth='')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask, sel):
    ''' Services a client connection represented by key. mask indicates the availible I/O operations (read, write).
    Read bytes the connection has delivered and send some out, as needed. 
    Whenever a complete request is recieved from the client (as detected by looking for the ternminal sequence '\\n\\n'), processes
    that request and registers the response to be sent back by appending it to the data attribute outb. When a client closes a connection,
    unregister the connection with the selector, and if they had logged in, unmark the bank account they were accessing as busy.  '''
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ: # Ready to read
        recv_data = sock.recv(1024)  
        if recv_data:
            data.inb += recv_data
            if is_complete(data.inb): # If the received data has the message termination sequence '\n\n':
                request = data.inb[:data.inb.rfind(b'\n\n')] # Strip the message termination and any odd stuff after that, just in case.
                print(f"Received request: {request !r} from the client.")
                data.outb += (process_request(request.decode(), data) + '\n\n').encode()
                data.inb = b'' # This request has been fully recevied and processed. No need to store it anymore.
        else: # Client sent empty message to indicate it is closing the connection.
            print(f"Closing connection to {data.addr}.")
            unmark_busy(acct_num=data.auth)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE: # Ready to write
        if data.outb:
            sent = sock.send(data.outb) 
            print(f"Sent {data.outb[:sent]!r} to {data.addr}")
            data.outb = data.outb[sent:]
            if data.outb:
                print(f"Remaining data to send: {data.outb!r}")

def is_complete(received:bytes) -> bool:
    '''True if received data has the termination sequence '\\n\\n', which means that the client has finished sending the message.
      False otherwise.'''
    return b'\n\n' in received

def process_request(request:str, session_data) -> str:
    '''Attempts to process the request from the client. session_data is data associated with this TCP session\n
    Valid requests are \n
    LOGIN acct_num pin\n
    BALANCE acct_num\n
    DEPOSIT acct_num amount\n
    WITHDRAW acct_num amount\n
    
    Returns response intended for client.
    This response includes a status code to indicate success or failure mode, 
    as well as optional data. \n
    '''
    try:
        request = request.split(' ')
        command = request[0]
        acct_num = request[1]        # Status code followed by text info that might help with debugging:
        if acct_num not in ALL_ACCOUNTS: return '400 Unknown Account Number'
             
        if command == 'LOGIN':
            print('Attempting Login.')
            return login(acct_num, request[2], session_data)
        elif command == 'BALANCE':
            print('Attempting To Get Balance.')
            return get_bal(acct_num, session_data)
        elif command == 'DEPOSIT':
            print('Attempting Deposit.')
            return deposit(acct_num, request[2], session_data)
        elif command == 'WITHDRAW':
            print('Attempting Withdrawl.')
            return withdraw(acct_num, request[2], session_data)
    except IndexError:
        pass
    return '400' # Malformed Request

def login(acct_num, pin, session_data):
    '''If the credentials are valid and the account is not busy, 
    update session_data to reflect that the client is now logged in and add to ACTIVE_ACCOUNTS to indicate the account is now busy.
    Returns response for client. The first line has the status code. If the account was busy but the credentials
    were valid, there is a second line with the IP address of the client currently accessing the account.'''
    if ALL_ACCOUNTS[acct_num].acct_pin == pin: # Correct Credentials.
        if acct_num in ACTIVE_ACCOUNTS: # But account is busy, can't be accessed.
            # First line: Status code
            # Second line: IP address of the client currently accessing the account
            return f'300\n{ACTIVE_ACCOUNTS[acct_num]}'
        # Successful Login!
        # Mark this account as busy:
        mark_busy(acct_num, busyIP=session_data.addr[0]) # addr takes the form (host IP, port number). Just want the IP.
        # if the client was already logged into a different account, unmark that one as busy.
        if session_data.auth and session_data.auth != acct_num: 
            unmark_busy(acct_num)
        # Identifies that the client is authorized to access this account:
        session_data.auth = acct_num
        return '200' # Success!
    else: 
        return '405' # Invalid Credentials


def mark_busy(acct_num, busyIP):
    '''Marks the given account number as busy so another client can't access it at the same time.
    Associates the IP address of the client that's currently accessing the account with the account number.'''
    ACTIVE_ACCOUNTS[acct_num] = busyIP
    print(f'Account {acct_num} is now being accessed by client at {busyIP}.')

def unmark_busy(acct_num):
    '''Unmarks the given account number as busy so another client can access it.'''
    if acct_num in ACTIVE_ACCOUNTS:
        del ACTIVE_ACCOUNTS[acct_num]
        print(f'Account {acct_num} freed up for access.')

def get_bal(acct_num, session_data):
    '''Get account balance associated with the given account number. The client must be logged in first.'''
    if acct_num != session_data.auth:
        # Either the client is not logged in or they are trying to access an account other than the one they logged into.
        return '401' # Unauthorized
    bal = ALL_ACCOUNTS[acct_num].acct_balance
    return f'200\n{bal}'

def deposit(acct_num, amount, session_data):
    '''Make a deposit in the specified account. The client must be logged in, and the amount must be a postive value representable in
    US currency (i.e. no more than two decimal places).'''
    if acct_num != session_data.auth:
        # Either the client is not logged in or they are trying to access an account other than the one they logged into.
        return '401' # Unauthorized
    status_code = ALL_ACCOUNTS[acct_num].deposit(as_numeric(amount))
    if status_code == 0:
        return '200' # Successful Deposit
    else: # Was not a postive value with no more than two decimal places.
        return '400 Invalid Deposit Amount'
    
def withdraw(acct_num, amount, session_data):
    '''Make a withdrawl from the specified account. The client must be logged in, and the amount must be a postive value representable in
    US currency (i.e. no more than two decimal places).'''
    if acct_num != session_data.auth:
        # Either the client is not logged in or they are trying to access an account other than the one they logged into.
        return '401' # Unauthorized
    status_code = ALL_ACCOUNTS[acct_num].withdraw(as_numeric(amount))
    if status_code == 0:
        return '200' # Successful Withdrawl
    elif status_code == 1: # Was not a postive value with no more than two decimal places
        return '400 Invalid Withdrawl Amount'
    elif status_code == 2:
        return '403' # Attempted Overdraft


##########################################################
#                                                        #
# Bank Server Demonstration                              #
#                                                        #
# Demonstrate basic server functions.                    #
# No changes needed in this section.                     #
#                                                        #
##########################################################

def demo_bank_server():
    """ A function that exercises basic server functions and prints out the results. """
    # get the demo account from the database
    acct = get_acct("zz-99999")
    print(f"Test account '{acct.acct_number}' has PIN {acct.acct_pin}")
    print(f"Current account balance: {acct.acct_balance}")
    print(f"Attempting to deposit 123.45...")
    code = acct.deposit(123.45)
    if not code:
        print(f"Successful deposit, new balance: {acct.acct_balance}")
    else:
        print(f"Deposit failed!")
    print(f"Attempting to withdraw 123.45 (same as last deposit)...")
    code = acct.withdraw(123.45)
    if not code:
        print(f"Successful withdrawal, new balance: {acct.acct_balance}")
    else:
        print("Withdrawal failed!")
    print(f"Attempting to deposit 123.4567...")
    code = acct.deposit(123.4567)
    if not code:
        print(f"Successful deposit (oops), new balance: {acct.acct_balance}")
    else:
        print(f"Deposit failed as expected, code {code}") 
    print(f"Attempting to withdraw 12345.45 (too much!)...")
    code = acct.withdraw(12345.45)
    if not code:
        print(f"Successful withdrawal (oops), new balance: {acct.acct_balance}")
    else:
        print(f"Withdrawal failed as expected, code {code}")
    print("End of demo!")

##########################################################
#                                                        #
# Bank Server Startup Operations                         #
#                                                        #
# No changes needed in this section.                     #
#                                                        #
##########################################################

if __name__ == "__main__":
    # on startup, load all the accounts from the account file
    load_all_accounts(ACCT_FILE)
    # uncomment the next line in order to run a simple demo of the server in action
    #demo_bank_server()
    run_network_server()
    print("bank server exiting...")
