### POST https://titleId.playfabapi.com/Authentication/GetEntityToken
Request Body
REQUEST BODY
Name	Type	Description
CustomTags	
object
The optional custom tags associated with the request (e.g. build numbe
externalnal trace identifiers, etc.).

Entity	
EntityKey
The entity to perform this action on.
Responses
RESPONSES
Name	Type	Description
200 OK	
404 OK
500 OK504 OK
GetEntityTokenResponse
200 Request	
ApiWrapper
