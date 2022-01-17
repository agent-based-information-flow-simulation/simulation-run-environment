package updateAgent

import org.apache.kafka.streams.StreamsConfig
import org.apache.kafka.streams.scala.serialization.Serdes

import java.util.Properties

object Config {
  val properties: Properties = {
    val props = new Properties()
    props.put(
      StreamsConfig.APPLICATION_ID_CONFIG,
      "UpdateAgentDataTransformerApp"
    )
    props.put(
      StreamsConfig.BOOTSTRAP_SERVERS_CONFIG,
      scala.util.Properties
        .envOrElse("BOOTSTRAP_SERVER", "EnvBootstrapServerNotDefined")
    )
    props.put(
      StreamsConfig.DEFAULT_KEY_SERDE_CLASS_CONFIG,
      Serdes.stringSerde.getClass
    )
    props
  }
}
