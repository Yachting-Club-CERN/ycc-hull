# User Roles - WIP

*This is part of the idea garden for now, but it would be nice to map permissions (admin, committee, regatta
organiser, key/licence holder) to roles.*

YCC key related roles:

* `KEY_D`
* `KEY_Y`

Teacher roles:

* `TEACHER_D`
* `TEACHER_Y`

## Administrator and Special roles

YCC Hull translates the rights encoded as bits from the database  (`ADMIN.RIGHTS`) to user roles.

*TODO Do we really want to translate?*

| Flag | Code | Role | Description |
|------|------|------|-------------|
| 1    |      |      |             |
| 2    |      |      |             |
| 4    |      |      |             |

* `1` `(R)`: Reservations admin
* `4 (M)`: `VIEW_MEMBER_DETAILS`

## Documentation of the Perl+Oracle System by Enrico

Ported from https://gitlab.cern.ch/ycc/reservation_system/-/blob/master/README.txt for reference.

```
ADMIN TABLE : 
R=Reservations
K=Keys (Versoix)
M= Members details
L=Licence registration
A= Administrator (not sure what special right this one is but only few people
have it :-) (comment by E.B. this allows some people to use members_info.pl to edit the fields of other users)

The table to update is ADMIN, the bits coding is:
1 R
2 K
4 M
8 L
16 A

and it is based on the binary system

so 
0= nothing
2=K
3=RK
15=RKML 
31=RKMLA
---------------------------------------------

...

09-11-2007	E. Bravin
```