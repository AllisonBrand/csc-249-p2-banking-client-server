#!/usr/bin/env python3
#
# Automated Teller Machine (ATM) client application.

import socket
import time

HOST = "127.0.0.1"      # The bank server's IP address
PORT = 65432            # The port used by the bank server

##########################################################
#                                                        #
# ATM Client Network Operations                          #
#                                                        #
# NEEDS REVIEW. Changes may be needed in this section.   #
#                                                        #
##########################################################

def send_to_server(sock, msg):
    """ Given an open socket connection (sock) and a string msg, send the string to the server. """
    # TODO make sure this works as needed
    return sock.sendall(msg.encode('utf-8'))

def get_from_server(sock, timeout=5):
    """ Attempt to receive a message from the active connection. Block until message is received, or timeout (specified in seconds) occurs.
     A message ends on a empty line ('\\n\\n') """
    msg = bytearray()
    ind = 0 # TODO make sure this works as needed
    start_time = time.time() 
    while not b'\n\n' in msg[ind:]: # While we still haven't seen an empty line,
        ind = len(msg)              # keep listening to receive messages from the server.
        msg.extend(sock.recv(1024))
        if time.time() - start_time > timeout: # Timeout for safety.
            raise TimeoutError
    # Great, we saw the end of the message.                     
    # Convert from bytearray to string, split on newlines.
    response = msg.decode('utf-8').split("\n") # The first line of response is the status line. 
    status_line = response[0].split(" ", maxsplit=1) # The status line is a status code followed by an optional text message for debugging.
    status_code = status_line[0]
    # The optional second line of the response is the data payload. If there is no payload, this will be an empty string.
    data = response[1]
    return status_code, data

def login_to_server(sock, acct_num, pin):
    """TODO Attempt to login to the bank server. 
    Pass acct_num and pin, get response, parse and check whether login was successful. \n
    Returns two values: (validated, busyIP).\n
    validated - True if the credentials were accepted.\n
    busyIP - If the account is busy, the IP address of the computer that's currently accessing it. None otherwise."""
    validated = False # True if the credentials were accepted.
    busyIP = None # If the account is busy, the IP address of the computer that's currently accessing it.
    send_to_server(sock, f"LOGIN {acct_num} {pin}\n\n")
    token, data = get_from_server(sock)
    if token == '200':
        validated = True
    elif token == '300':
        validated = True
        busyIP = data
    # token == '400': Login failed. The defaults for validated (False) and busyIP (None) are correct.
    return validated, busyIP

def get_login_info():
    """ Get info from customer. Validates the format of account number and pin and prompts user again as needed."""
    acct_num = input("Please enter your account number: > ")
    while not validAcctNumber(acct_num):
        acct_num = input(f'"{acct_num}" is not a valid account number. \
              Please enter an account number in the form: AA-NNNNN \
              where AA are two alphabetic characters (case-insensitive) and NNNNN are five numeric characters: > ')
    pin = input("Please enter your four digit PIN: > ")
    while not validPin(pin):
        pin = input(f'"{pin}" is not a valid PIN. Please enter your four digit PIN: > ')
    return acct_num, pin

def process_deposit(sock, acct_num):
    """Allows the user to deposit in their account. """
    bal = get_acct_balance(sock, acct_num)
    amt = input(f"How much would you like to deposit? (You have ${bal} available in account {acct_num}). > ").strip()
    # Input checking:
    # Reprompts the user if amt isn't numeric and positive. Rounds to the nearest cent.
    amt = ensure_valid(amt, min=0, err_msg="Deposit amount must be a postive dollar value.") 
    if not amt: # Failed to ensure valid
        print("Deposit transaction canceled.")
        return
    # Check that amt is positive.
    # Send the deposit request to the server.
    # The server could respond with success or authorization failure.
    # The client code only uses this method after a successful login, so this method doesn't 
    #    expect to receive authorization failure. 
    #    There is no special processing for errors.
    send_to_server(sock, f"DEPOSIT {acct_num} {amt}\n\n")
    token, _ = get_from_server(sock)
    if token.startswith('2'):
        print(f"Deposit of ${amt} completed. New balance: ${bal + amt}")
    else:
        print("Unrecognized response from server. Please try again later.")
    return

def get_acct_balance(sock, acct_num):
    """ Ask the server for current account balance. 
    Returns balance (as a string) on success, None on failure.  """
    send_to_server(sock, f"BALANCE {acct_num}\n\n")
    token, bal = get_from_server(sock)
    if token.startswith('2'):
        return bal
    else:
        print("Unrecognized response from server. Please try again later.")
    return None

def process_withdrawal(sock, acct_num):
    """Allows the user to withdraw from their account. """  
    bal = get_acct_balance(sock, acct_num)
    if bal is None: # Failed to properly communicate with server.
        return
    amt = input(f"How much would you like to withdraw? (You have ${bal} available in account {acct_num}). > ")
    # Input checking:
    # Reprompts the user if amt isn't numeric or is an attempted overdraft. Rounds to the nearest cent.
    amt = ensure_valid(amt, min=float(bal), err_msg="Attempted Overdraft. Your account balance cannont be debt.") 
    if not amt: # Failed to ensure valid withdrawl amount.
        print("Withdraw transaction canceled.")
        return
    # Send the withdraw request to the server.
    # The server could respond with either success, authorization failure, or forbidden attempted overdraw.
    # The client code only uses this method after a successful login, and this method check for overdraw before
    #    contacting the server. This method doesn't expect to receive either of those failure messages
    #    and has no special processing for errors.
    send_to_server(sock, f"WITHDRAW {acct_num} {amt}\n\n")
    token, _ = get_from_server(sock)
    if token.startswith('2'):
        print(f"Withdrawal of ${amt} completed. Remaining balance: ${bal - amt}")
    else:
        print("Unrecognized response from server. Please try again later.")
    return

def process_customer_transactions(sock, acct_num):
    """ Ask customer for a transaction, communicate with server."""
    while True:
        print("Select a transaction. Enter 'd' to deposit, 'w' to withdraw, or 'x' to exit.")
        req = input("Your choice? > ").lower()
        if req not in ('d', 'w', 'x'):
            print("Unrecognized choice, please try again.")
            continue
        if req == 'x':
            # if customer wants to exit, break out of the loop
            break
        elif req == 'd':
            process_deposit(sock, acct_num)
        else: # req == 'w'
            process_withdrawal(sock, acct_num)

def run_atm_core_loop(sock):
    """ Given an active network connection to the bank server, run the core business loop. 
    Return True on successful transactions, False otherwise. This can inform the message displayed to user on termination."""
    try:
        acct_num, pin = get_login_info()
        validated, busyIP = login_to_server(sock, acct_num, pin)
        if validated:
            print("Thank you, your credentials have been validated.")
            if busyIP:
                print(f" Unfortunately, your account is busy. The active user has IP address {busyIP}. \n" +
                    "If you do not recognize this activity please contact us immediately via our imaginary " +
                    "phone number, as we are not actually a bank.")
                return False
            process_customer_transactions(sock, acct_num)
            return True
        else:
            print("Account number and PIN do not match.")
            return False
    except TimeoutError:
        print("Server never responded.")
        return False

##########################################################
#                                                        #
# ATM Client Helpers for Network Operations                          #
#                                                        #
##########################################################

def validAcctNumber(acct_num):
    """Return True if acct_num represents a valid account number. 
    This does NOT test whether the account actually exists, only
    whether the value of acct_num is properly formatted to be used 
    as an account number.  A valid account number must be a string,
    lenth = 8, and match the format AA-NNNNN where AA are two alphabetic 
    characters and NNNNN are five numeric characters."""
    return isinstance(acct_num, str) and \
        len(acct_num) == 8 and \
        acct_num[2] == '-' and \
        acct_num[:2].isalpha() and \
        acct_num[3:8].isdigit()

def validPin(pin):
    """Return True if pin represents a valid PIN number. A valid PIN number 
    is a four-character string of only numeric characters."""
    return (isinstance(pin, str) and \
        len(pin) == 4 and \
        pin.isdigit())

def as_numeric(amount):
    '''If the amount is numeric (can be converted to float using Python's float() method),
    return as float. Otherwise, return None.'''
    try:
       return float(amount)
    except ValueError:
        return None
    
def ensure_valid(amt:str, min=None, err_msg='') -> str:
    '''Checks that amount is numeric, has no more than two decimal places, and is and greater than min, if min is specified. 
    If not, prompts the user to renter. err_msg is the complaint displayed to the user if the 
    input amount is less than or equal to min.
    Repeats until it can return string amount, 
    or returns False if the user chooses to break the loop. '''
    while True:
        if amt.lower() == 'x': # User wishes to exit.
                print('Apologies for the difficulty.')
                return False
        numeric_amt = as_numeric(amt)
        if numeric_amt is None: # Input wasn't numeric
            amt = input(f"Could not coerce {amt} to dollar value. Please enter again. ('x' to go back). > ").strip()
            continue
        if numeric_amt != round(numeric_amt, 2): # Input had more than two decimal places
            print(f"Cannot represent {numeric_amt} in US currency. Rounding to the nearest cent: ${round(numeric_amt, 2)}.")
            amt = input("Hit enter to proceed, or re-enter the deposit ammount. >").strip()
            if not amt: # The user just hit enter, indicating acceptance of the rounded deposit amount:
                numeric_amt = round(numeric_amt, 2)
            else:       # The user re-entered an amount
                continue
        if min is not None: # Ok, we should check that amount is greater than min:
            if numeric_amt <= min: # Input was numeric, but too low a value.
                if err_msg: print(err_msg, end=' ') 
                amt = input(f"Please enter again. ('x' to go back). > ").strip()
                continue
        # At this point, we know amt is numeric and greater than min
        return str(numeric_amt)

##########################################################
#                                                        #
# ATM Client Startup Operations                          #
#                                                        #
# No changes needed in this section.                     #
#                                                        #
##########################################################

def run_network_client():
    """ This function connects the client to the server and runs the main loop. 
     Return True on successful transactions, False otherwise. This can inform the message displayed to user on termination. """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            return run_atm_core_loop(s)
    except Exception as e:
        print(f"Unable to connect to the banking server - exiting...")

if __name__ == "__main__":
    print("Welcome to the ACME ATM Client, where customer satisfaction is our goal!")
    if run_network_client(): # It returns true on successful transaction.
        #  If the customer did not have a successful transaction, the below message would feel all the more insincere:
        print("Thanks for banking with us! Come again soon!!")
    print("ATM session terminating.")