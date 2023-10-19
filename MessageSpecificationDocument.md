# Summary
The client can attempt to login, view account balance, and make deposits or withdrawls. It's messages must conform to one of these 4 commands.
Responses from the server consist of a status code indicating success or the failure mode, data as relevant, and may also include some text for debugging purposes. Messages from both client and server terminate with an empty line, indicated with two consecutive linefeeds ("\n\n").

All client requests must include the account number, so an attacker can't simply send withdrawl requests to every server port until it finds one that is serving a logged-on client. This way, the attacker must guess the account number and the port of an authenticated connection. That ups the number of possible guesses from ~16,000 (the number of dynamic ports) to ~68,000,000 (the number of unique account numbers). I still wouldn't trust it, computers are fast. If the account number matches the one authorized for the socket, the server allows it to go through.

**Only one client may access an account at a time.** When a client successfully logs in, the account number is added to an internal dictionary and associated with the IP address of the client. If a client provides valid credentials but their account is in the dictionary, the client receives a failure message with the IP address of the user who is accessing their account.  

The client logs out by closing their connection with the server. There is no functionality to create new accounts. When the server exits, it save the changes to account balances in accounts.txt, overwriting all the comments in that file.

# Messages from the Client
```
; Augmented Backus–Naur form specification for messages sent by the client:

client-message = (login-cmd / balance-cmd / deposit-cmd / withdraw-cmd) 2LF

; Login Command: (SP stands for a single space character, %s means the literal text that follows is case sensitive)
login-cmd = %s"LOGIN" SP acct-num SP pin
acct-num = 2ALPHA "-" 5DIGIT
pin = 4DIGIT

; Balance Command:
balance-cmd = %s"BALANCE" SP acct-num

; Deposit Command:
deposit-cmd = %s"DEPOSIT" SP acct-num SP amount
amount = 1*DIGIT / (*DIGIT "." *2DIGIT) ; A positive number with at most two digits - a negative number or zero will still be understood by the server, but not processed

; Withdraw Command:
withdraw-cmd = %s"WITHDRAW" SP acct-num SP amount
```
## Example Requests: 
* `LOGIN ac-12345 1324`
* `BALANCE ac-12345`
* `DEPOSIT ac-12345 301.0`
* `WITHDRAW ac-12345 10.0`

# Messages from the Server
```
; Augmented Backus–Naur form specification for responses sent by the server:

server-resp = status-code [SP description] [LF data] 2LF

status-code = 3DIGIT
description = 1*(VCHAR / WSP) ; Optional info that might help the client developer with debugging
data = 1*(VCHAR / WSP)
```
The status codes are defined below. "x" stands for any digit.
2xx is a success. 
3xx is a failure that did not result from the client or server doing something wrong.
4xx is a client error.
I based it of the HTTP status codes.

| **Status Code**    | Interpretation |
| -------- | ------- |
| 200 | Success |
| 300 | Client credentials are correct, but account is busy.  |
| 400 | Malformed request |
| 401 | Client is not authorized to do this. |
| 403 | Attempted overdraft |
| 405 | Invalid login credentials |

## Example Requests: 
* ```
  200
  ```
* ```
  300
  131.229.63.0
  ```
* ```
  400 Invalid Deposit Amount
  ``` 
