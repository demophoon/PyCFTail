import keyring
import pinder
import sys
import signal
import time
from datetime import datetime, date, timedelta
import pytz
import argparse

# TODO:
# Cache user names to keep API calls down


def sigintHandler(signum, frame):
    # handler for SIGINT signal
    print "Caught SIGINT. Exiting."
    sys.exit(0)


def parseCommandlineArgs():
    parser = argparse.ArgumentParser(description="Stalk Campfire room without needing to join")
    parser.add_argument("-e", "--environment", help="Keyring environment to use to pull API Token", default="campfire")
    parser.add_argument("-d", "--domain", help="Campfire domain to use", required=True)
    parser.add_argument("-l", "--local_timezone", help="Local timezone for use when displaying timestamps", default="America/Chicago")
    parser.add_argument("-r", "--room", help="Campfire room to stalk. Can be numerical room ID or string name", required=True)
    return parser.parse_args()


def getCFAPIToken(environment, domain):
    #Gets the password out of keyring. "username" is the subdomain we connect to. See the
    # campfire API for more information on the subdomain
    kr = keyring.get_keyring()
    return kr.get_password(environment, domain)


def findCFRoom(cf, room_id):
    # find a campfire room. If an integer is passed in, assume this is the numerical room ID
    # otherwise, assume it's a string that is the room name.
    if (room_id.isdigit()):
        return cf.room(room_id)
    else:
        return cf.find_room_by_name(room_id)


def getUsername(cf, message):
    # Gets the username of the user creating the message. Sometimes this is "None",
    #  so we call that a "__System__" message
    if (message['user_id'] is None):
        return "__System__"
    else:
        return cf.user(message['user_id'])['user']['name']


def getMessageBody(message):
    # Gets the message text. Sometimes the message text is "None" and we want to display
    #   something different based on the type of message
    type = message['type']
    if (type == "TextMessage"):
        return message['body']
    elif (type == "PasteMessage"):
        return message['body']
    elif (type == "EnterMessage"):
        return "Entered Room"
    elif ((type == "LeaveMessage") or (type == "KickMessage")):
        return "Left Room"
    elif (type == "AllowGuestsMessage"):
        return "Guest access enabled"
    elif (type == "DisallowGuestsMessage"):
        return "Guest access disabled"
    else:
        return "Other message: Type: %s ; Body: %s" % (message['type'], message['body'])


def getLocalDateTime(destTZ, timeString):
    # convert the UTC timestamp from the message into the local timezone.
    if destTZ is None:
        # if no timezone is defined, just return the UTC string
        return timeString

    # instantiate the local timezone and the UTC timezone objects
    localtz = pytz.timezone(destTZ)
    utc = pytz.timezone('UTC')

    # convert the time string to a datetime object
    dt = datetime.strptime(timeString, "%Y/%m/%d %H:%M:%S +0000")

    # magic from here on out
    utc.localize(dt)
    dt = utc.localize(dt)
    return dt.astimezone(localtz).strftime("%c")


def main():
    # register the CTRL+C event handler
    signal.signal(signal.SIGINT, sigintHandler)

    # parse command line arguments
    args = parseCommandlineArgs()

    # log into campfire
    cf = pinder.Campfire(args.domain, getCFAPIToken(args.environment, args.domain))

    # make sure we got logged in
    if (not isinstance(cf, pinder.Campfire)):
        print "Unable to log into campfire.\n"
        sys.exit(1)

    # obtain the room name
    room = findCFRoom(cf, args.room)

    # make sure room was found
    if (not isinstance(room, pinder.Room)):
        print "Unable to find room %s\n" % sys.argv[1]
        sys.exit(1)

    last_message_id = None
    max_messages = 0
    # start the listener for room events
    while 1:
        if (last_message_id is None):
            # first time in loop. just pull the last 10 messages
            max_messages = 10
        else:
            max_messages = 100

        # print the recent messages
        for message in room.recent_messages(limit=max_messages, since_message_id=last_message_id):
            # set the last message ID
            last_message_id = message['id']

            # We dont care about sound messages or timestamp messages
            if ((message['type'] == "SoundMessage") or (message['type'] == "TimestampMessage")):
                continue

            # print the message
            username = getUsername(cf, message)
            timestamp = getLocalDateTime(args.local_timezone, message['created_at'])
            body = getMessageBody(message)
            print "(%s)%s: %s" % (timestamp, username, body)

        # wait a few seconds, then do it all again
        time.sleep(5)

if __name__ == '__main__':
    main()
