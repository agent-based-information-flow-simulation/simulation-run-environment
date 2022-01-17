UNWIND $batch as event
MATCH (agent:Agent {jid: event.properties.jid, simulation_id: event.properties.simulation_id})
OPTIONAL MATCH (agent)-[relationship]->()
SET agent = event.properties
DELETE relationship

WITH DISTINCT agent, event
UNWIND event.connections as connection_list
WITH agent, connection_list.name AS connection_list_name, connection_list.to as connection_list_to, event
UNWIND connection_list_to as to
MATCH (to_agent:Agent {jid: to, simulation_id: event.properties.simulation_id})
CALL apoc.create.relationship(agent, connection_list_name, {r_type: 'connection'}, to_agent) YIELD rel

WITH DISTINCT agent, event
UNWIND event.messages as message_list
WITH agent, message_list.name AS message_list_name, message_list.messages as message_list_messages, event
UNWIND message_list_messages as message
MATCH (to_agent:Agent {jid: message.sender, simulation_id: event.properties.simulation_id})
CALL apoc.create.relationship(agent, message_list_name, message, to_agent) YIELD rel
RETURN NULL
