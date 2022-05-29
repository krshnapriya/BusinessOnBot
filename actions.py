# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

import typing
from typing import Any, Text, Dict, List, Union, Optional

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
import requests, json

class ValidateUserDetailsForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_user_details_form"

    async def required_slots(
        self,
        slots_mapped_in_domain: List[Text],
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: "DomainDict",
    ) -> Optional[List[Text]]:
        
        required_slots = []
        if tracker.latest_message["intent"].get("name") == "corona_help":
            required_slots = ["confirm_pin_code", "confirm_resource_category"]
        else:
            required_slots = ["pin_code", "category"]

        return required_slots

    
    def validate_pin_code(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        print("HERE1")
        url = f"https://api.postalpincode.in/pincode/{slot_value}"
        r = requests.get(url)
        data = json.loads(r.content)
        status = data[0]['Status']
        print(status)

        if status == 'Error':
            dispatcher.utter_message(text="Invalid PIN code.")
            return {"pin_code": None}
        else:
            return {"pin_code": slot_value}

    def validate_category(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        url = "http://ec2-3-23-130-174.us-east-2.compute.amazonaws.com:8000/categories"
        r = requests.get(url)
        data = json.loads(r.content)
        category_list = data["data"]
        if slot_value not in category_list:
            dispatcher.utter_message(text="This resource is currently not available. Please choose another.")
            return {"category": None}
        else:
            return {"category": slot_value}

    def validate_confirm_pin_code(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        pin_code = tracker.get_slot("pin_code")

        if slot_value.lower() == 'no':
            return {"pin_code": None}
        else:
            return {"pin_code": pin_code}


    def validate_confirm_resource_category(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        category = tracker.get_slot("category")
        if slot_value.lower() == "no":
            return {"category": None}
        else:
            return {"category": category}


    
class ActionSubmit(Action):
    def name(self) -> Text:
        return "action_submit"

    def run(
        self,
        dispatcher,
        tracker: Tracker,
        domain: "DomainDict",
    ) -> List[Dict[Text, Any]]:

        pin_code = tracker.get_slot("pin_code")
        category = tracker.get_slot("category")
        pin_code_url = f"https://api.postalpincode.in/pincode/{pin_code}"
        r1 = requests.get(pin_code_url)
        data1 = json.loads(r1.content)
        city = data1[0]['PostOffice'][0]['District']
        city_url = "http://ec2-3-23-130-174.us-east-2.compute.amazonaws.com:8000/cities"
        r2 = requests.get(city_url)
        data2 = json.loads(r2.content)
        cities = data2['data']

        if city in cities:
            city = city.replace(" ", "%20")
            category = category.replace(" ", "%20")
            category_url = f"http://ec2-3-23-130-174.us-east-2.compute.amazonaws.com:8000/resource?city={city}&category={category}"
            r = requests.get(category_url)
            data = json.loads(r.content)
            data = data['data']

            if not data:
                result = "No resources found."
                dispatcher.utter_message(response="utter_submit",
                                    pin_code=pin_code,
                                    category=category,
                                    contact = result,
                                    description = result,
                                    organisation = result,
                                    phone = result,
                                    state = result)
                return []

            contact = data[0]["contact"]
            description = data[0]["description"]
            organisation = data[0]["organisation"]
            phone = data[0]["phone"]
            state = data[0]["state"]

            category = category.replace("%20", " ")

            dispatcher.utter_message(response="utter_submit",
                                    pin_code=pin_code,
                                    category=category,
                                    contact = contact,
                                    description = description,
                                    organisation = organisation,
                                    phone = phone,
                                    state = state
                                    )
        
        else:
            result = "No resources found."
            dispatcher.utter_message(response="utter_submit",
                                    pin_code=pin_code,
                                    category=category,
                                    contact = result,
                                    description = result,
                                    organisation = result,
                                    phone = result,
                                    state = result)