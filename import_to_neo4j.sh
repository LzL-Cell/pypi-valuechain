#!/bin/bash
set -e

NEO4J_BIN=/home/lzl/neo4j/bin/cypher-shell
CSV_DIR=/home/lzl/example/pypi-valuechain/workspace/csvs

echo "[Neo4j] Creating constraints..."

$NEO4J_BIN <<EOF
CREATE CONSTRAINT method_name IF NOT EXISTS
FOR (m:Method) REQUIRE m.fullName IS UNIQUE;

CREATE CONSTRAINT function_name IF NOT EXISTS
FOR (f:Function) REQUIRE f.name IS UNIQUE;

CREATE CONSTRAINT package_name IF NOT EXISTS
FOR (p:Package) REQUIRE p.name IS UNIQUE;
EOF

echo "[Neo4j] Importing CSVs..."

for method_csv in "$CSV_DIR"/*_methods.csv; do
  pkg=$(basename "$method_csv" _methods.csv)
  call_csv="$CSV_DIR/${pkg}_calls.csv"

  echo "[Neo4j] Importing package: $pkg"

  $NEO4J_BIN <<EOF
MERGE (p:Package {name: "$pkg"});

LOAD CSV FROM 'file:///${method_csv}' AS row
MERGE (m:Method {fullName: row[0]})
MERGE (p)-[:HAS_METHOD]->(m);
EOF

  if [ -f "$call_csv" ]; then
    $NEO4J_BIN <<EOF
LOAD CSV FROM 'file:///${call_csv}' AS row
MERGE (caller:Method {fullName: row[0]})
MERGE (callee:Function {name: row[1]})
MERGE (caller)-[:CALLS]->(callee);
EOF
  fi
done

echo "[Neo4j] Import completed."
