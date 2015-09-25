##Major Changes

###2015-08-18
####Breaking Changes

The password hashing mechanism has changed.

This change has some additional python dependencies, explicitly bcrypt and 
passlib.  Additionally, there is a consideration to make when upgrading an 
old installation to the latest build.  Specifically, the password hash field 
width has to change in addition to making a decision regarding the legacy, 
weak, hashes.  The recommended approach is to use a script similar to 
[this](https://github.com/hlainchb/datazoomer/blob/master/setup/database/upgrade_hash_db.py)
which will adjust the field width for you as well as temporarily improving 
the hash that DataZoomer stores.  Alternatively, you could update the field 
width manually and have DataZoomer update the hashes automatically 
at each users next visit.  This approach is not optimal in that the weak hash 
will continue to be stored until such time as the users next login, which 
unfortunately could be never.

[Commits](https://github.com/hlainchb/datazoomer/compare/285c83f8c3283a93d8aa79e63e40610f52a55ad0...20ef555f7be0478f0d8ebf75a70a46b3a78db58c)

