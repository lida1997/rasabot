# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"


#
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import typing
from typing import Dict, Text, Any, List

from neo4j import GraphDatabase
from rasa_sdk.events import SlotSet

uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(uri, auth=False)

def get_attr_of(tx, name, attr):
    result = tx.run(f"MATCH (n:Product) WHERE n.name= $name return n.{attr} AS res", name=name)

    return [record["res"] for record in result][0]

def get_attrs(tx, attr):
    result = tx.run(f"MATCH (n:Product)  return n.{attr} AS res")

    return [record["res"] for record in result]

def get_product_of(tx,attr,order):
    result = tx.run(f"MATCH (n:Product)  return n.name ,n.{attr} as res ORDER BY n.price DESC")

    return [(record["n.name"],record["res"]) for record in result][order]

def get_products(tx):
    products = []
    result = tx.run("MATCH (n:Product)  return n.name AS product")
    for record in result:
        products.append(record["product"])
    return products
#
class ActionUtterProductScene(Action):
#
    def name(self) -> Text:
        return "action_utter_productScene"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        transform_dic = {'优势':'strength',
                       '介绍':'info',
                       '报价':'price',
                       '解读项':'items'}
        product, scene = tracker.get_slot("product"),tracker.get_slot("scene")
        with driver.session() as session:
            res = session.read_transaction(get_attr_of, product,transform_dic[scene])
            dispatcher.utter_message(text=f"{product}的{scene}是：{res}")
        return []


class ActionCompareAttr(Action):

    def name(self) -> Text:
        return "action_compare_attr"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        transform_dic = {'优势':'strength',
                       '介绍':'info',
                       '报价':'price',
                       '解读项':'items'}
        scene = None
        try:
            scene = next(tracker.get_latest_entity_values("scene"))
        except:
            scene = tracker.get_slot("scene")
        finally:
            if scene is None:
                scene = '报价'
        text_order = {-1:"最便宜",
                      0:"最贵",
                      1:"第二贵"}
        order =  int(next(tracker.get_latest_entity_values("order")))-1
        with driver.session() as session:
            product,res = session.read_transaction(get_product_of, transform_dic[scene],order)
            dispatcher.utter_message(text=f"{text_order[order]}的产品是{product}，它的{scene}是：{res}")
        return [SlotSet("scene",scene),SlotSet("product",product)]

class ActionUtterWhat(Action):

    def name(self) -> Text:
        return "action_utter_what"
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        product = None
        try:
            product = next(tracker.get_latest_entity_values("product"))
        except:
            product = tracker.get_slot("product")
        finally:
            if product is None:
                dispatcher.utter_message(text="您想问什么产品的介绍？")
                return [SlotSet("scene",'介绍')]

        with driver.session() as session:
            res = session.read_transaction(get_attr_of, product,'info')
            dispatcher.utter_message(text=f"{product}的介绍是：{res}")
        return [SlotSet("scene",'介绍'),SlotSet("product",product)]