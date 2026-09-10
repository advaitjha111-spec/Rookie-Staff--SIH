"use client";

import { Background, Controls, MiniMap, ReactFlow, type Edge, type Node } from "@xyflow/react";
import type { EvidenceResult } from "@/types/forensics";

export function CampaignGraph({ data }: { data: EvidenceResult }) {
  const nodes: Node[] = [{ id: "evidence", position: { x: 0, y: 115 }, data: { label: `Evidence\n${data.ingestion.hash_sha256.slice(0, 12)}…` }, type: "default" }];
  const edges: Edge[] = []; const add = (id: string, label: string, y: number) => { nodes.push({ id, position: { x: 320, y }, data: { label } }); edges.push({ id: `e-${id}`, source: "evidence", target: id, animated: true }); };
  if (data.forensics.origin_ip) add("origin", `Origin IP\n${data.forensics.origin_ip}`, -30); 
  if (data.metadata.from) add("sender", `Claimed sender\n${data.metadata.from}`, 115); 
  if (data.ai_analysis?.threat_actor_claimed) add("actor", `Claimed actor\n${data.ai_analysis.threat_actor_claimed}`, 260);
  return <section className="intel-visual"><div className="visual-title"><p className="eyebrow">Campaign relationships</p><span>Only entities returned by this case</span></div><div className="campaign-graph"><ReactFlow nodes={nodes} edges={edges} fitView proOptions={{ hideAttribution: true }}><Controls /><Background /></ReactFlow></div></section>;
}
