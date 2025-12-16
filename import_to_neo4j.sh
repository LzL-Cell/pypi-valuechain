#!/bin/bash

NEO4J_HOME=~/neo4j
CSV_DIR=$NEO4J_HOME/import/csvs

for m in $CSV_DIR/*_methods.csv; do
  pkg=$(basename "$m" _methods.csv)
  calls="$CSV_DIR/${pkg}_calls.csv"

  echo "Importing $pkg"

  cypher-shell <<EOF
LOAD CSV FROM 'file:///csvs/${pkg}_methods.csv' AS row
WITH row[0] AS fullName
MERGE (:Method {fullName: fullName});

LOAD CSV FROM 'file:///csvs/${pkg}_calls.csv' AS row
WITH row[0] AS caller, row[1] AS callee
MERGE (m:Method {fullName: caller})
MERGE (f:Function {name: callee})
MERGE (m)-[:CALLS]->(f);
EOF

done
