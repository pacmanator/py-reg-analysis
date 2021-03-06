import datetime
import winreg as reg


__author__ = "pacmanator"
__email__ = "mrpacmanator at gmail dot com"
__version__ = "v1.0"


# Not readable characters to name a file or directory
NOT_READABLE_CHARS = [chr(character) for character in range(0, 32)]
NOT_READABLE_CHARS += [chr(character) for character in range(33, 40)]
NOT_READABLE_CHARS += ["*", ">", "<", "\"", ":", "?", "\\", "/", "|"]
NOT_READABLE_CHARS += ["^", "=", "@", "}", "{", ";", "[", "]", "+"]


def remove_chars(key_value):
    """ This function removes the not readable characters and
        the not allowed files characters from a string.
    """
    filename = list()
    for byte in key_value:

        try:
            char = chr(byte).encode('utf-8')
            readable_char = chr(ord(char))

            if not (readable_char in NOT_READABLE_CHARS):
                filename.append(readable_char)
            else:
                continue

        # Some windows registry keys has a two-bytes value
        # this exception skips that encoding error.
        except TypeError:
            continue

    return "".join(filename)


def user2sid(user_name):
    """
        Returns the user id of the provided user name.
        @param user_id: The user name.
    """
    path = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList"

    # Opens the specified key path.
    with reg.OpenKeyEx(reg.HKEY_LOCAL_MACHINE, path) as key:

        # Iterates through each sub key.
        for inx in range(reg.QueryInfoKey(key)[0]):
            
            key_name = reg.EnumKey(key, inx)

            # Retrieves information of the provided profile key.
            with reg.OpenKeyEx(key, key_name) as user_key:

                # Get the name of the user from its profileImagePath key value.
                profile_image_path = reg.QueryValueEx(user_key, "ProfileImagePath")[0]
                user_name_index = profile_image_path.rfind("\\") + 1

                # Return the user identification if it matches the provided user name
                if user_name.lower() == profile_image_path[user_name_index:].lower():
                    return key_name


def get_time(windows_time):
    """
        Converts a windows time to a UTC time.
        @param windows_time: 64-bits Windows timestamp.
    """
    time = datetime.datetime(1601,1,1) + datetime.timedelta(microseconds=windows_time//10)
    return "{0} UTC".format(time.ctime())


def users_list():
    """ 
        Returns the sid of non-system users.
    """
    # A list of existing users.
    users = list()

    # Path to the users profile list HKEY.
    PATH = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList"

    # Open the users HKEY with the Profile list path as sub key.
    with reg.OpenKeyEx(reg.HKEY_LOCAL_MACHINE, PATH) as userList:

        # Obtain the amount of sub keys in the userList HKEY.
        numSubKeys = reg.QueryInfoKey(userList)[0]

        for user in range(0, numSubKeys):
            
            # Excludes the system accounts.
            if reg.EnumKey(userList, user).startswith("S-1-5-21"):
                users.append(reg.EnumKey(userList, user))
            else:
                continue

    return users


def parse_mru_inx(mru_list_ex):
    """
        Return an index of the most recently opened files.
        @param mru_list_ex: MRUListEx value.
    """
    # MRU files index.
    file_inx = list()

    # Iterates through the whole MRUListEx value in bytes chunks.
    for inx in range(0, len(mru_list_ex) - 4, 4):
        # Divides de MRUListEx into chunks of 4 bytes.
        chunk = mru_list_ex[inx:inx + 4]

        # Adds the hexadecimal values of the provided MRUListEx chunk.
        file_inx.append(sum([chunk[inx]  for inx in range(4)]))

    return file_inx


def get_normal_user_name(user_sid):
    """
        Return the name of a non-system user, based on it's sid.
        @param: user_sid: Windows user identifier.
    """
    user_name = None
    try:
        path = "{0}\\Volatile Environment".format(user_sid)
        with reg.OpenKeyEx(reg.HKEY_USERS, path) as key:
            user_name = reg.QueryValueEx(key, "USERNAME")[0]
    
    except FileNotFoundError:
        pass
    
    except Exception as e:
        raise Exception(e)

    return user_name


def get_system_user_name(user_sid):
    """
        Return the name of a system user, based on it's sid.
        @param: user_sid: Windows user identifier.
    """
    user_name = None
    try:
        path = "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\{0}".format(user_sid)
        with reg.OpenKeyEx(reg.HKEY_LOCAL_MACHINE, path) as key:
            user_name = reg.QueryValueEx(key, "ProfileImagePath")[0]

            # String index of the '\' character.
            inx = user_name.rfind("\\") + 1

            # Where does starts the name of the user.
            user_name = user_name[inx:]
    
    except FileNotFoundError:
        pass
    
    except Exception as e:
        raise Exception(e)

    return user_name


def get_user_name(user_sid):
    """
        Returns if the user sid belongs to a system user or to a non-system user.
        @param user_sid: Windows-user identification.
    """
    user_type, user_name = "Non-system", get_normal_user_name(user_sid)

    if user_name is None:
        user_type, user_name = "System", get_system_user_name(user_sid)
    
    return user_type, user_name
