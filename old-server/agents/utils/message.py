import json
import random as rand
import uuid
from types import SimpleNamespace

NUM_TOPICS = 5


class Message:
    w = [1, 1, 1, 1, 1, 1]  # temporary solution

    def __init__(self, jid=""):
        """Creates a message instance


        Before using the message further methods need be called
        jid -- creator's jid
        """
        self.creator_jid = str(jid)

    def new(self, topic):
        """Generates new random message

        topic -- message's topic
        """
        self.id = uuid.uuid4().int  # each msg gets a unique incremented id
        self.parent_id = self.id
        self.emotion = {
            "attitude": rand.uniform(-1.0, 1.0),
            "arousal": rand.uniform(-1.0, 1.0),
        }
        self.persuation = rand.uniform(0, 1)
        self.journalistic = rand.uniform(0, 1)
        self.clickbait = rand.uniform(0, 1)
        self.images = rand.uniform(0, 1)
        self.topic = topic
        self.debunking = False
        self.debunk_id = -1

    def new_debunk(self, debunk_id, debunk_topic):
        """Generates new debunking message for a given fake news

        debunk_id -- id of the message we are debunking
        debunk_topic -- topic of the message we are debunking
        """
        self.id = uuid.uuid4().int  # each msg gets unique incremented id
        self.parent_id = self.id
        self.emotion = {
            "attitude": rand.uniform(-1.0, 1.0),
            "arousal": rand.uniform(-1.0, 1.0),
        }
        self.persuation = rand.uniform(0, 1)
        self.journalistic = rand.uniform(0, 1)
        self.clickbait = rand.uniform(0, 1)
        self.images = rand.uniform(0, 1)
        self.topic = debunk_topic
        self.debunking = True
        if debunk_id < 0:
            raise ValueError("Id of the message must be a positive integer!")
        self.debunk_id = debunk_id

    def mutate(self):
        self.id = uuid.uuid1().int
        to_evolve = rand.randint(0, 5)
        if to_evolve == 0:
            self.emotion["attitude"] = rand.uniform(-1.0, 1.0)
        elif to_evolve == 1:
            self.emotion["arousal"] = rand.uniform(-1.0, 1.0)
        elif to_evolve == 2:
            self.persuation = rand.uniform(0, 1)
        elif to_evolve == 3:
            self.journalistic = rand.uniform(0, 1)
        elif to_evolve == 4:
            self.clickbait = rand.uniform(0, 1)
        elif to_evolve == 5:
            self.images = rand.uniform(0, 1)

    @staticmethod
    def fromJSON(msg_json):
        """Loads message data from a JSON string

        msg_json - json represenation of a message
        """
        ret = Message()
        tmp = json.loads(msg_json, object_hook=lambda d: SimpleNamespace(**d))
        ret.id = tmp.id
        ret.parent_id = tmp.parent_id
        ret.topic = tmp.topic
        ret.creator_jid = tmp.creator_jid
        ret.emotion = {}
        ret.emotion["attitude"] = tmp.emotion.attitude
        ret.emotion["arousal"] = tmp.emotion.arousal
        ret.persuation = tmp.persuation
        ret.journalistic = tmp.journalistic
        ret.clickbait = tmp.clickbait
        ret.images = tmp.images
        ret.debunking = tmp.debunking
        ret.debunk_id = tmp.debunk_id
        return ret

    def toJSON(self):
        """Converts a Message into a JSON and returns as string"""
        return json.dumps(self.__dict__)

    def calculate_power(self):
        return (
            (
                Message.w[0] * self.emotion["attitude"]
                + Message.w[1] * self.emotion["arousal"]
                + Message.w[2] * self.persuation
                + Message.w[3] * self.journalistic
                + Message.w[4] * self.clickbait
                + Message.w[5] * self.images
            )
            * 100
            / sum(Message.w)
        )
