import enum
import json
import requests
import os
from typing import Union
from dotenv import load_dotenv

class MediaType(enum.Enum):
    Text = 1
    Image = 2


class Category(enum.Enum):
    Hate = 1
    SelfHarm = 2
    Sexual = 3
    Violence = 4


class Action(enum.Enum):
    Accept = 1
    Reject = 2


class DetectionError(Exception):
    def __init__(self, code: str, message: str) -> None:

        self.code = code
        self.message = message

    def __repr__(self) -> str:
        return f"DetectionError(code={self.code}, message={self.message})"


class Decision(object):
    def __init__(
        self, suggested_action: Action, action_by_category: dict[Category, Action]
    ) -> None:

        self.suggested_action = suggested_action
        self.action_by_category = action_by_category


class ContentSafety(object):
    def __init__(self, endpoint: str, subscription_key: str, api_version: str) -> None:

        self.endpoint = endpoint
        self.subscription_key = subscription_key
        self.api_version = api_version

    def build_url(self, media_type: MediaType) -> str:

        if media_type == MediaType.Text:
            return f"{self.endpoint}/contentsafety/text:analyze?api-version={self.api_version}"
        elif media_type == MediaType.Image:
            return f"{self.endpoint}/contentsafety/image:analyze?api-version={self.api_version}"
        else:
            raise ValueError(f"Invalid Media Type {media_type}")

    def build_headers(self) -> dict[str, str]:

        return {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "Content-Type": "application/json",
        }

    def build_request_body(
        self,
        media_type: MediaType,
        content: str,
        blocklists: list[str],
    ) -> dict:

        if media_type == MediaType.Text:
            return {
                "text": content,
                "blocklistNames": blocklists,
            }
        elif media_type == MediaType.Image:
            return {"image": {"content": content}}
        else:
            raise ValueError(f"Invalid Media Type {media_type}")

    def detect(
        self,
        media_type: MediaType,
        content: str,
        blocklists: list[str] = [],
    ) -> dict:

        url = self.build_url(media_type)
        headers = self.build_headers()
        request_body = self.build_request_body(media_type, content, blocklists)
        payload = json.dumps(request_body)

        response = requests.post(url, headers=headers, data=payload)
        print(response.status_code)
        print(response.headers)
        print(response.text)

        res_content = response.json()

        if response.status_code != 200:
            raise DetectionError(
                res_content["error"]["code"], res_content["error"]["message"]
            )

        return res_content

    def get_detect_result_by_category(
        self, category: Category, detect_result: dict
    ) -> Union[int, None]:

        category_res = detect_result.get("categoriesAnalysis", None)
        for res in category_res:
            if category.name == res.get("category", None):
                return res
        raise ValueError(f"Invalid Category {category}")

    def make_decision(
        self,
        detection_result: dict,
        reject_thresholds: dict[Category, int],
    ) -> Decision:

        action_result = {}
        final_action = Action.Accept
        for category, threshold in reject_thresholds.items():
            if threshold not in (-1, 0, 2, 4, 6):
                raise ValueError("RejectThreshold can only be in (-1, 0, 2, 4, 6)")

            cate_detect_res = self.get_detect_result_by_category(
                category, detection_result
            )
            if cate_detect_res is None or "severity" not in cate_detect_res:
                raise ValueError(f"Can not find detection result for {category}")

            severity = cate_detect_res["severity"]
            action = (
                Action.Reject
                if threshold != -1 and severity >= threshold
                else Action.Accept
            )
            action_result[category] = action
            if action.value > final_action.value:
                final_action = action

        if (
            "blocklistsMatch" in detection_result
            and detection_result["blocklistsMatch"]
            and len(detection_result["blocklistsMatch"]) > 0
        ):
            final_action = Action.Reject

        print(final_action.name)
        print(action_result)

        return Decision(final_action, action_result)


if __name__ == "__main__":

    load_dotenv() 

    endpoint = os.getenv("AZURE_CONTENTSAFETY_ENDPOINT")
    subscription_key = os.getenv("AZURE_CONTENTSAFETY_KEY")
    api_version = "2023-10-01"

    content_safety = ContentSafety(endpoint, subscription_key, api_version)

    media_type = MediaType.Text
    blocklists = []

    content = "<test_content>"

    detection_result = content_safety.detect(media_type, content, blocklists)

    reject_thresholds = {
        Category.Hate: 4,
        Category.SelfHarm: 4,
        Category.Sexual: 4,
        Category.Violence: 4,
    }

    decision_result = content_safety.make_decision(detection_result, reject_thresholds)