package updateAgent

import scala.util.Properties

object Topics {
  val UpdateAgentInput: String = Properties.envOrElse(
    "UPDATE_AGENT_INPUT_TOPIC_NAME",
    "EnvUpdateAgentInputTopicNameNotDefined"
  )
  val UpdateAgentOutput: String = Properties.envOrElse(
    "UPDATE_AGENT_OUTPUT_TOPIC_NAME",
    "EnvUpdateAgentOutputTopicNameNotDefined"
  )
}
