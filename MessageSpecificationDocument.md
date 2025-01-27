# Summary
The client can attempt to login, view account balance, and make deposits or withdrawls. It's messages must conform to one of these 4 commands.
Responses from the server consist of a status code indicating success or the failure mode, data as relevant, and may also include some text for debugging purposes. Messages from both client and server terminate with an empty line, indicated with two consecutive linefeeds ("\n\n").

All client requests must include the account number, so an attacker can't simply send withdrawl requests to every server port until it finds one that is serving a logged-on client. This way, the attacker must guess the account number and the port of an authenticated connection. That ups the number of possible guesses from ~16,000 (the number of dynamic ports) to ~68,000,000 (the number of unique account numbers). If the account number matches the one authorized for the socket, the server allows it to go through. I still wouldn't trust it, computers are fast. 

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

Deposit or Withdrawl amounts are specified in dollars. For the server to allow the transaction, the amount must be postive, nonzero, and have no more than two decimal places  (two decimal places is the greatest precision supported by US currency). The withdrawl amount cannot exceed the account balance. It would have been less complicated and less error prone (floating point rounding error) if I had represented account balances as integer numbers of cents (¢). This would have required rewritting a large enough amount of code that I decided not to do it. 


## Example Requests: 
* `LOGIN ac-12345 1324\n\n`
* `BALANCE ac-12345\n\n`
* `DEPOSIT ac-12345 301.0\n\n`
* `WITHDRAW ac-12345 10.0\n\n`

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

## Example Responses: 
* ```
  200\n\n
  ```
* ```
  300 The data carried in this request is the IP address of the client currently accessing account.\n
  131.229.63.0\n\n
  ```
* ```
  400 Blah, blah, blah! Does anyone read these debbugging messages?\n\n
  ```

  # Example Communications:

For readability, I drop the message termination sequence '\n\n', but it is still required.

| **Client 1 Requests**  | **Server Response to Client 1** | **Client 2 Requests**  |  **Server Response to Client 2** |
| :--------: | :-------: | :-------: | :-------: |
| LOGIN ac-12345 1324 | 200 | | |
|BALANCE ac-12345|200\n1307.32| | |
| | |LOGIN ac-12345 1324| 300\n127.0.0.1 |
| WITHDRAW wf-14351 0.02 | 200 | | | 
|BALANCE ac-12345 | 200\n1307.3 | | |
| | | LOGIN fe-63912 0000 | 405 Server closes connection. |
|DEPOST ac-12345 -200 |400 Invalid Deposit Amount| | |
