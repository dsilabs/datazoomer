"""
    DataZoomer auth

    TODO: add scrypt support when introduced into passlib (v1.7)
"""
try:
    from passlib.context import CryptContext
    from handlers import DataZoomerSaltedHash, BcryptDataZoomerSaltedHash, BcryptMySQL41, BcryptMySQL323

    __all__ = ['ctx']

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
except ImportError:
    ctx = None
    DataZoomerSaltedHash, BcryptDataZoomerSaltedHash = None, None
    __all__ = ['ctx']
except:
    raise