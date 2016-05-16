"""
    DataZoomer auth

    TODO: add scrypt support when introduced into passlib (v1.7)
"""

__all__ = ['validate_password', 'hash_password']

def get_context(date_added):
    """create a password encryption context"""
    try:
        from passlib.context import CryptContext
        from handlers import (
            DataZoomerSaltedHash,
            BcryptDataZoomerSaltedHash,
            BcryptMySQL41,
            BcryptMySQL323,
        )

        salt = '{:%Y-%m-%d %H:%M:%S}'.format(date_added)
        salt_function = lambda a: salt
        DataZoomerSaltedHash.salt_fn = salt_function
        BcryptDataZoomerSaltedHash.salt_fn = salt_function

        context = CryptContext(
            schemes=[
                "bcrypt_sha256",
                BcryptDataZoomerSaltedHash,
                BcryptMySQL41,
                BcryptMySQL323,
                DataZoomerSaltedHash,
                "mysql41",
                "mysql323"
            ],

            default="bcrypt_sha256",

            deprecated=[
                "bcrypt_sha256_dz_weak_salt",
                "bcrypt_sha256_mysql41",
                "bcrypt_sha256_mysql323",
                "datazoomer_weak_salt",
                "mysql41",
                "mysql323"
            ],

            # vary rounds parameter randomly when creating new hashes...
            all__vary_rounds = 0.1,

            # logarithmic, 2**{rounds} and bound from 4 to 31
            bcrypt_sha256__rounds = 14,
            bcrypt_sha256_dz_weak_salt__rounds = 14,
            bcrypt_sha256_mysql41__rounds = 14,
            bcrypt_sha256_mysql323__rounds = 14,
        )

    except ImportError:
        context = None
        DataZoomerSaltedHash, BcryptDataZoomerSaltedHash = None, None

    except:
        raise

    return context

def validate_password(password, stored_password_hash, date_added):
    """validate a password and return the best hash
    
    Validates the supplied password to see if it matches the stored password
    based one of the accepted algorythms and also returns a hash based on the
    best algorythm that is currently supported.  This allows passwords stored
    with older algorythms to be accepted while providing the ability to
    contantly upgrade algorythms as they improve.
    """
    context = get_context(date_added)
    return context.verify_and_update(password, stored_password_hash)

def hash_password(password, date_added):
    """hash a password"""
    context = get_context(date_added)
    return context.encrypt(password)

