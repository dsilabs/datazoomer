""" Prepare a legacy DataZoomer password database for use with the new hash mechanism (e.g. bcrypt).  Additionally, it
    temporarily (until the user next hits the site) stores a stronger hash (a stronger hash of the weak hash).

    e.g. usage: python upgrade_hash_db.py --database=some_db_name --user=zoom --pwd=testme --do


    Notes:
        i. It is recommended to take the site offline before you upgrade the DataZoomer library and run this script.
           This will ensure nobody hits the site, which will force a new hash of the password yet get trimmed/corrupted
           when writing it to the database.  This will be due to the fact that the field width is too small.
        i. An optional approach is to increase the field width manually and then update the DataZoomer library.  The
           new hash mechanism will now be used for each user.  However, this leaves a hole in that the legacy outdated hashes
           will be left in the database until a user next hits the site (this is not optimal).
        i. We will use our own CryptContext here as we expect zoom.auth to change over time.
        i. Run with the --help option to get a brief help message of the available options.
        i. The password database update requires python libs "bcrypt" and "passlib" which may require some development
           headers, depending on your system.
"""
import re
from passlib.context import CryptContext
from zoom.db import database
from zoom.auth.handlers import DataZoomerSaltedHash, BcryptDataZoomerSaltedHash, BcryptMySQL41, BcryptMySQL323

db = None
ctx = CryptContext(
    schemes=["bcrypt_sha256",
        BcryptDataZoomerSaltedHash, BcryptMySQL41, BcryptMySQL323,
        DataZoomerSaltedHash,
        "mysql41", "mysql323"
      ],
    default="bcrypt_sha256",
    deprecated=[
        "bcrypt_sha256_dz_weak_salt", "bcrypt_sha256_mysql41", "bcrypt_sha256_mysql323",
        "datazoomer_weak_salt",
        "mysql41", "mysql323"
      ],

    # vary rounds parameter randomly when creating new hashes...
    all__vary_rounds = 0.1,

    # logarithmic, 2**{rounds} and bound from 4 to 31
    bcrypt_sha256__rounds = 14,
    bcrypt_sha256_dz_weak_salt__rounds = 14,
    bcrypt_sha256_mysql41__rounds = 14,
    bcrypt_sha256_mysql323__rounds = 14,
    )


def get_pwd_field_length():
    fdef = list(db("describe dz_users password"))[0][1]
    return int(re.findall(r'\d+',fdef)[0])

def backup(nice=1):
    if 'dz_users_b' in [t for t, in db("show tables")]:
        raise RuntimeError('A backup already exists (we do not want to overwite the original backup with partial bcrypt converts!)')
    db("create table dz_users_b like dz_users;")
    db("insert into dz_users_b select * from dz_users;")

def reset():
    db("update dz_users a inner join dz_users_b b on a.userid=b.userid set a.password = b.password;")

def alter(chars=125):
    if get_pwd_field_length()<=chars:
        db("alter table dz_users change password password varchar(%s);" % chars)

def get_users():
    return list(db("select userid, loginid, password, date_format(dtadd,'%%Y-%%m-%%d %%H:%%i:%%s'), status from dz_users where password<>'' and password is not null"))

def pre_integrity_checks():
    users = get_users()
    # the expected passwords are the old mysql pwd hash or the new one
    for _, _, pwd, _, _ in users:
        if len(pwd) not in [16, 41]: raise RuntimeError('Integrity Error (we may have a db with partially converted passwords)')

    # assess pwd field length, alter should have been called already to increase the field width
    if get_pwd_field_length()<=41: raise RuntimeError('Field length is too small (@ {})'.format(get_pwd_field_length()))

def rehash_db():
    users = get_users()
    # rehash them
    # NOTE: this will be an issue if a site ever used PASSWORD() hash without the DataZoomer salt (dtadd)
    for pk, loginid, pwd, salt, status in users:
        version = len(pwd)
        dtadd = lambda a: salt
        DataZoomerSaltedHash.salt_fn = dtadd
        BcryptDataZoomerSaltedHash.salt_fn = dtadd
        hash = None
        if version==16: hash = ctx.encrypt(pwd, scheme='bcrypt_sha256').replace('$bcrypt-sha256$','$bcrypt-sha256-mysql323$')
        elif version==41: hash = ctx.encrypt(pwd, scheme='bcrypt_sha256').replace('$bcrypt-sha256$','$bcrypt-sha256-dz$')  # ** WARNING/NOTE above
        else: raise RuntimeError('Integrity Error')

        if hash is None or hash=='': raise RuntimeError('Hash Integrity Error')
        db("update dz_users set password=%s where userid=%s and loginid=%s", hash, pk, loginid)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", help="backup dz_users to dz_users_b", default=False, action="store_true")
    parser.add_argument("--reset", help="push the dz_users_b data back into dz_users", default=False, action="store_true")
    parser.add_argument("--alter", help="alter the password field length for dz_users", default=False, action="store_true")
    parser.add_argument("--checks", help="run the pre-hash integrity checks", default=False, action="store_true")
    parser.add_argument("--hash", help="perform the bcrypt hash on the database", default=False, action="store_true")
    parser.add_argument("--do", help="perform the backup, alter password hash field width and hash the weak hashes, all for the given database", default=False, action="store_true")
    parser.add_argument("--database", help="database to perform the operations against", default='zoomdata', action="store")
    parser.add_argument("--user", help="database user to use", default='zoom', action="store")
    parser.add_argument("--pwd", help="database user password to use", default='zoom', action="store")
    args = parser.parse_args()

    db = database(
        host='localhost',
        db=args.database,
        user=args.user,
        passwd=args.pwd,
        charset='utf8'
      )

    if args.backup:
        backup()
    if args.reset:
       reset()
    if args.alter:
       alter()
    if args.checks:
       pre_integrity_checks()
    if args.hash:
        pre_integrity_checks()
        rehash_db()
    if args.do:
       print 'Converting database {}'.format(args.database)
       backup()
       alter()
       pre_integrity_checks()
       rehash_db()

