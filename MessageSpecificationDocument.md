# Summary
The client can attempt to login, view account balance, and make deposits or withdrawls. It's messages must conform to one of these 4 commands: LOGIN, BALANCE, DEPOST, and WITHDRAW.
Responses from the server consist of a status code indicating success or the failure mode, data as relevant, and may also include some text for debugging purposes.

# Messages from the Client
```
; Augmented Backus–Naur form specification for messages sent by the client:

client-message = (login-cmd / balance-cmd / deposit-cmd / withdraw-cmd) "\n\n"

; Login Command: (WSP stands for a single space character, %s means the literal text that follows is case sensitive)
login-cmd = %s"LOGIN" WSP acct-num WSP pin
acct-num = 2ALPHA "-" 5DIGIT
pin = 4DIGIT


```
