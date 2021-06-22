Definitions
DEFINITIONS
ApiErrorWrapper
The basic wrapper around every failed API response

EntityKey
Combined entity 
type 
and 
ID structure which uniquely identifies a single entity.

GetEntityTokenRequest
This API must be called 
with 
X-SecretKey, X-Authentication 
or 
X-EntityToken headers. 
An 
optional EntityKey may be included to attempt to 
set 
the resulting EntityToken to a specific entity,
however the entity must be a relation of the caller, such 
as 
the master_player_account of a character. 
If 
sending X-EntityToken the account will be marked 
as 
freshly logged

 in and 
  will issue a new token. 
  If

 using X-Authentication 
or 
X-EntityToken the header must still be valid 
and

 cannot be expired 
  or 
  revoked.
