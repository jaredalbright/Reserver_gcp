# Pickleball Reserver #
This repo is a GCF that is meant to reserve Pickleball classes at a gym
### Example Payload ###
````
{
    "event_id": "id of class",
    "trigger_time": "HH:MM",
    "member_id": "id of member",
    "username": "email of member"
}
````
Note `trigger_time` is in UTC