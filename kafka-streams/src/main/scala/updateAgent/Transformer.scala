package updateAgent

import updateAgent.Domain._
import org.apache.kafka.streams.scala.ImplicitConversions._
import org.apache.kafka.streams.scala._
import org.apache.kafka.streams.KafkaStreams
import org.apache.kafka.streams.scala.serialization.Serdes._

object Transformer {
  val getProperties: Agent => AgentProperties = (agent: Agent) => {
    (agent.floats.++(agent.enums).++(agent.float_lists)
      + ("simulation_id" -> agent.simulationId) + ("jid" -> agent.jid) + ("type" -> agent.agentType))
      .asInstanceOf[AgentProperties]
  }

  val getConnections: Agent => AgentConnections = (agent: Agent) => {
    agent.connections
      .map(key_value => Connections(key_value._1, key_value._2))
      .toVector
  }

  val getMessages: Agent => AgentMessages = (agent: Agent) => {
    agent.messages
      .map(key_value => Messages(key_value._1, key_value._2))
      .toVector
  }

  def main(args: Array[String]): Unit = {
    val builder = new StreamsBuilder()
    builder
      .stream[Jid, Agent](Topics.UpdateAgentInput)
      .mapValues(agent =>
        UpdateAgentData(
          getProperties(agent),
          getConnections(agent),
          getMessages(agent)
        )
      )
      .to(Topics.UpdateAgentOutput)
    new KafkaStreams(builder.build(), Config.properties).start()
  }
}
