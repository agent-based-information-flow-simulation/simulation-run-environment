import agents
import random
import datetime
import json
import asyncio
from spade.behaviour import PeriodicBehaviour, CyclicBehaviour
from spade.agent import Agent
from spade.message import Message
import visualization
from agents.utils import Message as News
from agents.utils import calculate_accept

INIT_SUSCEPTIBILITY = 50  # TBD
DEBUNK_SUS_BOUNDRY = 20
BELIVER_SUS_BOUNDRY = 80
MAX_RECEIVE_TIME_SEC = 1000
MAX_INITIAL_DELAY_SEC = 30
MAX_SPREAD_INTERVAL_SEC = 10
MAX_CREATE_INTERVAL_SEC = 300
CONVERGENCE = 16
SEND_SELF_PERIOD_SEC = 5
MSG_MUTATE_PROBOBILITY = 1
FOLLOW_NEWS_CREATOR_PROBABILITY = 0.1
UNFOLLOW_NEWS_CREATOR_PROBABILITY = 1


class Common(Agent):
    def __init__(
        self, graph_creator_jid, jid, pswd, loc, adj, topic=0, verify_security=False
    ):
        super().__init__(jid, pswd, verify_security)
        self.location = loc
        self.adj_list = adj
        self.believing = []
        self.debunking = []
        self.graph_creator_jid = graph_creator_jid
        self.susceptibility = INIT_SUSCEPTIBILITY
        self.susceptible_topic = topic
        self.period_debunk = random.randint(3, MAX_SPREAD_INTERVAL_SEC)
        self.period_share = random.randint(3, MAX_SPREAD_INTERVAL_SEC)
        self.period_create = random.randint(60, MAX_CREATE_INTERVAL_SEC)
        self.delay = random.randint(1, MAX_INITIAL_DELAY_SEC)
        self.type = "common"
        self.state = "susceptible"

    def log(self, msg):
        full_date = datetime.datetime.now()
        time = datetime.datetime.strftime(full_date, "%H:%M:%S")
        print(f"[{time}] {str(self.jid)} {self.type[0].capitalize()}: {msg}")

    def setup(self):
        # self.log(
        #     f"common, location: {self.location}, neighbours: {len(self.adj_list)}, susceptible topic: {self.susceptible_topic}"
        # )

        self.accept_news_behaviour = self.AcceptNews()
        self.add_behaviour(self.accept_news_behaviour)

        start_at = datetime.datetime.now() + datetime.timedelta(seconds=self.delay)
        self.share_news_behaviour = self.ShareNews(
            period=self.period_share, start_at=start_at
        )
        self.add_behaviour(self.share_news_behaviour)

        start_at = datetime.datetime.now() + datetime.timedelta(seconds=self.delay)
        self.create_news_behaviour = self.CreateFakeNews(
            period=self.period_create, start_at=start_at
        )
        self.add_behaviour(self.create_news_behaviour)

        start_at = datetime.datetime.now() + datetime.timedelta(seconds=self.delay)
        self.debunk_behaviour = self.ShareDebunk(
            period=self.period_debunk, start_at=start_at
        )
        self.add_behaviour(self.debunk_behaviour)

        # self.send_self_to_visualization = self.SendSelfToVisualization(
        #     period=SEND_SELF_PERIOD_SEC, start_at=datetime.datetime.now()
        # )
        # self.add_behaviour(self.send_self_to_visualization)

    class AcceptNews(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(MAX_RECEIVE_TIME_SEC)

            if not msg:
                self.agent.log("timeout or received msg is empty")
                pass
            else:
                # read msg
                content = News.fromJSON(msg.body)

                if self.agent.state == "susceptible":
                    if (content not in self.agent.believing) and (
                        content not in self.agent.debunking
                    ):
                        # its math time
                        msg_power = content.calculate_power()
                        expected_score = 1 / (
                            1 + 10 ** ((msg_power - self.agent.susceptibility) / 50)
                        )
                        result = random.uniform(0, 100)
                        if result > calculate_accept(
                            msg_power, self.agent.susceptibility
                        ):  # accept the msg
                            # self.agent.log(f"BELIEVED {msg_power}")
                            #                  sus: {self.agent.susceptibility} \n
                            #                  sus_delta: {CONVERGENCE * (1 - expected_score)} \n
                            #                  result: {result} \n
                            #                  accept: {calculate_accept(msg_power, self.agent.susceptibility)}""")
                            self.agent.susceptibility = (
                                self.agent.susceptibility
                                + CONVERGENCE * (1 - expected_score)
                            )
                            if random.random() < FOLLOW_NEWS_CREATOR_PROBABILITY:
                                follow_request = Message()
                                follow_request.to = str(self.agent.graph_creator_jid)
                                follow_request.body = json.dumps(
                                    {"follow": content.creator_jid}
                                )
                                # await self.send(follow_request)

                            if content.debunking:
                                to_unfollow = [
                                    m
                                    for m in self.agent.believing
                                    if (
                                        m.id == content.debunk_id
                                        or m.parent_id == content.debunk_id
                                    )
                                ]

                                for msg in to_unfollow:
                                    if (
                                        random.random()
                                        < UNFOLLOW_NEWS_CREATOR_PROBABILITY
                                    ):
                                        unfollow_request = Message()
                                        unfollow_request.to = str(
                                            self.agent.graph_creator_jid
                                        )
                                        unfollow_request.body = json.dumps(
                                            {"unfollow": content.creator_jid}
                                        )
                                        # await self.send(unfollow_request)

                                self.agent.believing = [
                                    m
                                    for m in self.agent.believing
                                    if (
                                        m.id != content.debunk_id
                                        or m.parent_id != content.debunk_id
                                    )
                                ]
                            self.agent.believing.append(content)
                        else:  # refute the msg
                            # self.agent.log(f"REFUTED {msg_power}")
                            #                  sus: {self.agent.susceptibility} \n
                            #                  sus_delta: {CONVERGENCE * (- expected_score)} \n
                            #                  result: {result} \n
                            #                  accept: {calculate_accept(msg_power, self.agent.susceptibility)}""")
                            self.agent.susceptibility = (
                                self.agent.susceptibility
                                + CONVERGENCE * (-expected_score)
                            )
                            self.agent.debunking.append(content)
                        # self.agent.log(f"current sus: {self.agent.susceptibility}")
                        if self.agent.susceptibility < DEBUNK_SUS_BOUNDRY:
                            self.agent.state = "debunking"
                            self.agent.create_news_behaviour.kill(0)
                            self.agent.susceptibility = 0
                        if self.agent.susceptibility > BELIVER_SUS_BOUNDRY:
                            self.agent.state = "believing"
                            self.agent.debunk_behaviour.kill(0)
                            self.agent.susceptibility = 100
                    elif self.agent.state == "believing":
                        self.agent.believing.append(content)
                    elif self.agent.state == "debunking":
                        self.agent.debunking.append(content)

    class ShareNews(PeriodicBehaviour):
        async def run(self):
            if self.agent.adj_list and self.agent.believing:
                num_rand_recipients = random.randint(1, len(self.agent.adj_list))
                rand_recipients = random.sample(
                    self.agent.adj_list, k=num_rand_recipients
                )

                rand_believing_msg = random.choice(self.agent.believing)
                # self.agent.log(
                #     f"spreading believing news to {num_rand_recipients} recipients"
                # )

                if random.random() > MSG_MUTATE_PROBOBILITY:
                    rand_believing_msg.mutate()

                msgs = []
                msgs_to_visualize = []
                for recipient in rand_recipients:
                    msg = Message()
                    msg.to = recipient
                    msg.body = rand_believing_msg.toJSON()
                    msgs.append(msg)
                    msgs_to_visualize.append(
                        {
                            "from_jid": self.agent.jid,
                            "to_jid": recipient,
                            "type": "debunk"
                            if rand_believing_msg.debunking
                            else "fakenews",
                            "full_msg": rand_believing_msg,
                        }
                    )

                # visualization.post_messages(msgs_to_visualize)
                await asyncio.wait([self.send(msg) for msg in msgs])
            else:
                # self.agent.log(
                #     f"couldn't spread news, reason: neighbours: {len(self.agent.adj_list)}, believing: {len(self.agent.believing)}, debunking: {len(self.agent.debunking)}"
                # )
                pass

    class ShareDebunk(PeriodicBehaviour):
        async def run(self):
            if self.agent.adj_list and self.agent.debunking:
                num_rand_recipients = random.randint(1, len(self.agent.adj_list))
                rand_recipients = random.sample(
                    self.agent.adj_list, k=num_rand_recipients
                )
                to_debunk = random.choice(self.agent.debunking)

                debunk_msg = News(str(self.agent.jid))
                debunk_msg.new_debunk(to_debunk.id, to_debunk.topic)
                # self.agent.log(f"spreading debunk to {num_rand_recipients} recipients")
                msgs = []
                msgs_to_visualize = []
                for recipient in rand_recipients:
                    msg = Message()
                    msg.to = recipient
                    msg.body = debunk_msg.toJSON()
                    msgs.append(msg)
                    msgs_to_visualize.append(
                        {
                            "from_jid": self.agent.jid,
                            "to_jid": recipient,
                            "type": "debunk",
                            "full_msg": debunk_msg,
                        }
                    )

                # visualization.post_messages(msgs_to_visualize)
                await asyncio.wait([self.send(msg) for msg in msgs])
            else:
                # self.agent.log(
                #     f"couldn't spread debunk, reason: neighbours: {len(self.agent.adj_list)}, believing: {len(self.agent.believing)}, debunking: {len(self.agent.debunking)}"
                # )
                pass

    class CreateFakeNews(PeriodicBehaviour):
        async def run(self):
            if self.agent.adj_list:
                num_rand_recipients = random.randint(1, len(self.agent.adj_list))
                rand_recipients = random.sample(
                    self.agent.adj_list, k=num_rand_recipients
                )
                new_fake_news = News(str(self.agent.jid))
                new_fake_news.new(self.agent.susceptible_topic)
                self.agent.believing.append(new_fake_news)
                # self.agent.log(
                #     f"generating new fake news and spreading to {num_rand_recipients} recipients"
                # )

                msgs = []
                msgs_to_visualize = []
                for recipient in rand_recipients:
                    msg = Message()
                    msg.to = recipient
                    msg.body = new_fake_news.toJSON()
                    msgs.append(msg)
                    msgs_to_visualize.append(
                        {
                            "from_jid": self.agent.jid,
                            "to_jid": recipient,
                            "type": "fakenews",
                            "full_msg": new_fake_news,
                        }
                    )

                # visualization.post_messages(msgs_to_visualize)
                await asyncio.wait([self.send(msg) for msg in msgs])
            else:
                # self.agent.log(
                #     f"couldn't create fake news, reason: neighbours: {len(self.agent.adj_list)}, believing: {len(self.agent.believing)}, debunking: {len(self.agent.debunking)}"
                # )
                pass

    # class SendSelfToVisualization(PeriodicBehaviour):
    #     async def run(self):
    #         visualization.post_agent(self.agent)
