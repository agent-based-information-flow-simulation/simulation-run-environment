package updateAgent

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.databind.json.JsonMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule
import org.apache.kafka.common.serialization.Serde
import org.apache.kafka.streams.scala.serialization.Serdes

import scala.collection.immutable.HashMap

object Domain {
  type Timestamp = Int
  type SimulationId = String
  type Jid = String
  type AgentType = String
  type Message = HashMap[String, Any]
  type Enum = String

  case class Agent(
      @JsonProperty("__timestamp__") timestamp: Timestamp,
      @JsonProperty("simulation_id") simulationId: SimulationId,
      jid: Jid,
      @JsonProperty("type") agentType: AgentType,
      floats: HashMap[String, Float],
      connections: HashMap[String, Vector[Jid]],
      messages: HashMap[String, Vector[Message]],
      float_lists: HashMap[String, Vector[Float]],
      enums: HashMap[String, Enum]
  )

  type AgentProperty = Any
  type AgentProperties = HashMap[String, AgentProperty]

  case class Connections(
      name: String,
      to: Vector[Jid]
  )
  type AgentConnections = Vector[Connections]

  case class Messages(
      name: String,
      messages: Vector[Message]
  )
  type AgentMessages = Vector[Messages]

  case class UpdateAgentData(
      properties: AgentProperties,
      connections: AgentConnections,
      messages: AgentMessages
  )

  val jsonMapper: JsonMapper =
    JsonMapper.builder().addModule(DefaultScalaModule).build()

  implicit val serdesAgent: Serde[Agent] = {
    val serializer = (agent: Agent) => jsonMapper.writeValueAsBytes(agent)
    val deserializer = (bytes: Array[Byte]) =>
      Option(jsonMapper.readValue(new String(bytes), classOf[Agent]))
    Serdes.fromFn[Agent](serializer, deserializer)
  }

  implicit val serdesUpdateAgentData: Serde[UpdateAgentData] = {
    val serializer = (agent: UpdateAgentData) =>
      jsonMapper.writeValueAsBytes(agent)
    val deserializer = (bytes: Array[Byte]) =>
      Option(jsonMapper.readValue(new String(bytes), classOf[UpdateAgentData]))
    Serdes.fromFn[UpdateAgentData](serializer, deserializer)
  }
}
