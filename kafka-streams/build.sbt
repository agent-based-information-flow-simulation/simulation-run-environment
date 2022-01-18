ThisBuild / version := "0.1.0-SNAPSHOT"

ThisBuild / scalaVersion := "2.12.15"

libraryDependencies ++= Seq(
  "org.apache.kafka" %% "kafka-streams-scala" % "3.0.0",
  "com.fasterxml.jackson.module" %% "jackson-module-scala" % "2.13.1",
  "org.slf4j" % "slf4j-simple" % "1.7.32"
)

ThisBuild / assemblyMergeStrategy := {
  case PathList("META-INF", _*) => MergeStrategy.discard
  case _                        => MergeStrategy.first
}

lazy val root = (project in file("."))
  .settings(
    name := "kafka-streams"
  )
