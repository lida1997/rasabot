from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=False)


def get_attr(tx, name, attr):
    result = tx.run(f"MATCH (n:Product) WHERE n.name= $name return n.{attr} AS res", name=name)

    return [record["res"] for record in result][0]


def get_products(tx):
    products = []
    result = tx.run("MATCH (n:Product)  return n.name AS product")
    for record in result:
        products.append(record["product"])
    return products

with driver.session() as session:
    res = session.read_transaction(get_attr, "ASA","items")
    print(res)

driver.close()