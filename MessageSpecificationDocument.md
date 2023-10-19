# Summary
The client can attempt to login, view account balance, and make deposits or withdrawls. It's messages must conform to one of these 4 commands: LOGIN, BALANCE, DEPOST, and WITHDRAW.
Responses from the server consist of a status code indicating success or the failure mode, data as relevant, and may also include some text for debugging purposes. Messages terminate with an empty line, indicated with two consecutive linefeeds ("\n\n") 

Only one 

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
The client attempts to login with a LOGIN command.

# Messages from the Server
```
; Augmented Backus–Naur form specification for responses sent by the server:

server-resp = status-code [SP description] [LF data] 2LF

status-code = 3DIGIT
description = 1*(VCHAR / WSP) ; Optional info that might help the client developer with debugging
data = 1*(VCHAR / WSP)
```
The status codes are defined below. In the table "x" stands for any digit.
Anything that starts with 2 is a success. 
Anything that starts with 3 is a failure that did not result from the client or server doing something wrong.
Anything that starts with 4 is a client error.
I based it of the HTTP status codes.

| **Status Code**    | Interpretation |
| -------- | ------- |
| 2xx  | Success  |
| 300 | Credentials are correct, but account is busy   |
| March    | $420    |
