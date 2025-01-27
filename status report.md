# P2 design requirements you believe you have satisfied:
## General Project Requirements

- [x] You MUST use the provided bank_server and atm_client programs as your starting point. You MUST NOT implement your own bank server and client from scratch.
- [x] You MAY extend the core banking functionality in the bank_server and atm_client, but only to the degree needed to enable the two components to be able to interoperate.
- [x] Your code MUST be readable, well organized, and demonstrate care and attention to computer programming best practices. The provided bank_server and atm_client provide good examples of such practices: classes and functions with easy-to-understand names are used extensively; functions are kept short (under 20 lines is ideal); functions are commented, and comments are inserted at key points within the function body.

## Bank Server Requirements 
I tested the ones with double checkmarks ✔✔.

- [x] MUST run in its own computing process (i.e., in a dedicated terminal window). ✔✔
- [x] MUST allow multiple simultaneous ATM client connections.  ✔✔
- [x] MUST communicate with ATM clients exclusively by sending and receiving messages over the network using an application-layer message protocol of your own design. ✔✔
- [x] MUST allow multiple ATM clients to send messages to the server and receive timely responses from the server. One client should never be blocked until other client(s) have completed all their transactions.  ✔✔
- [x] MUST validate an account's PIN code before allowing any other transactions to be performed on that account. - My client doesn't let you do that, but I believe my code satisfies this.
- [x] MUST prevent more than one ATM client at a time from accessing a bank account and performing transactions on it.  ✔✔
- [x] MUST transmit error results to the client using numeric codes rather than literal message strings. ✔✔
- [x] After a customer "logs in" to their account from an ATM client, the server MUST allow any number of transactions to be performed during that client banking session. During the session, access to the account from other ATM clients MUST be rejected.  ✔✔
- [x] MUST prevent malicious client applications (i.e., other than the implemented atm_client application) from being able to send messages the the server which cause the server to crash, behave incorrectly, and/or provide unauthorized access to customer bank accounts.  ✔✔
- [x] The bank_server MAY generate console output for tracing and debugging purposes.  ✔✔
- [x] The bank_server MUST NOT assume that any customer has access to the server's console.

## ATM Server Requirements
I tested the ones with double checkmarks ✔✔.

- [x] MUST run in its own computing process (i.e., in a dedicated terminal window).  ✔✔
- [x] MUST obtain all needed user inputs through keyboard interaction.   ✔✔
- [x] MUST connect to only one bank_server at a time.
- [x] MUST communicate with the bank_server exclusively by sending and receiving messages over the network using an application-layer message protocol of your own design.  ✔✔
- [x] MUST require each banking session to being with a customer "log in" step, where the customer provides an account number and PIN which are then validated by the bank_server.  ✔✔
- [x] MUST NOT allow a customer to perform any banking transactions unless their account number and PIN are first validated by the bank_server.  ✔✔
- [x] MUST allow a customer to perform any sequence of deposits, withdrawals, and balance checks after they have validated their account number and PIN.  ✔✔
- [x] MUST NOT allow a customer to overdraw their bank account.  ✔✔

## Message Specification Requirements

- [x] This document MUST include a written summary of the application-layer message protocol you developed for all communications between the client and the server.
- [x] Message formats MUST be documented using Augmented Backus–Naur form (ABNF). See <https://en.wikipedia.org/wiki/Augmented_Backus%E2%80%93Naur_form> for details on ABNF.
- [x] In addition to the ABNF specification, you MUST include some examples of each type of message you have defined.
- [ ] You MUST describe the component fields of each message, what constitutes allowed values for each field, and expected receiver actions in response to each message. - I detailed some, but not all receiver responses for every kind of client request. I did describe the component fields of each message, and what constitutes allowed values for each field.
- [x] You MUST include a brief description of how you solved the design problem of preventing bank account access from more than one atm_client at a time.

(I learned how to make checkboxes from Brendan's Slack post from Oct. 5th, and this checkbox list was simply copy-pasted from that post).

# Top 3 most significant knowledge or understanding gaps that are standing in your way, and any thoughts you have about what you might do to overcome those gaps. 
The challenge was simply the amount of time it took. I'm spending much more than the expected 12 hours per week for this 4 credit class. Being given so much code and having to read over and understand all of was very time-consuming. I appreciated the specific deliverable guidelines, but with the amount of code I had to read through, figure out connections between, and modify, it would've been quicker to simply write my own.  Being given the BankAccount class was helpful. I didn't have to modify it, so I didn't have to spend time figuring out its implementation details. I think that this project should've been spread out in 2 projects, or the deadline should've been further off. 

I do have a question: in the ABNF specification, do you specify only the messages that will be successfully executed by the server, or the messages that the server can interpret?

I imagine that this status report would be approximately one page in length, maybe a bit more though probably not a bit less. The idea is to help me understand what you've accomplished, and what's holding you back. And also what your thoughts are for how you could be part of the solution!
