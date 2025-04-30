# ruff: noqa: E501

import asyncio
import json
import time

from django.conf import settings
from langchain_community.chat_models.fake import FakeListChatModel


class MyFakeListChatModel(FakeListChatModel):
    delay: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.delay = kwargs.get("delay", settings.FAKE_LLM_DELAY)
        self.sleep = 0.002

    def _call(self, *args, **kwargs):
        response = self.responses[self.i]
        if "error" in response:
            msg = "Fake error"
            raise ValueError(msg)
        if self.delay > 0:
            time.sleep(self.delay)
        return super()._call(*args, **kwargs)

    async def _astream(self, *args, **kwargs):
        response = self.responses[self.i]
        if "error" in response:
            msg = "Fake error"
            raise ValueError(msg)
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        async for chunk in super()._astream(*args, **kwargs):
            yield chunk


def get_fake_llm_model(name):
    if name == "skeleton":
        return MyFakeListChatModel(responses=[json.dumps(skeleton_json)])
    if name == "continuation":
        # Add "error" in the response to test the error handling
        return MyFakeListChatModel(responses=["This is a continuation of the story"])
    if name == "ending":
        return MyFakeListChatModel(responses=["This is the ending of the story."])
    if name == "text_explanation":
        return MyFakeListChatModel(responses=["This is the explanation of the text."])
    if name == "scene_generation":
        return MyFakeListChatModel(responses=[json.dumps(scenes_json)])
    return None


scenes_json = {
    "scenes": [
        {
            "level": "A1",
            "text": "A test scene in A1",
        },
        {
            "level": "A2",
            "text": "A test scene in A2",
        },
        {
            "level": "B1",
            "text": "A test scene in B1",
        },
        {
            "level": "B2",
            "text": "A test scene in B2",
        },
        {
            "level": "C1",
            "text": "A test scene in C1",
        },
        {
            "level": "C2",
            "text": "A test scene in C2",
        },
    ],
}

skeleton_json = {
    "story_background": "A mysterious series of events unfolds in the small coastal town of Seabreeze, where a once-peaceful community becomes embroiled in secrets, betrayal, and the quest for truth after a local fisherman disappears under suspicious circumstances.",
    "milestones": [
        {
            "milestone_id": "M1",
            "description": "The disappearance of Joe, a local fisherman, is reported to the town sheriff.",
            "decision_points": [
                {
                    "decision_point_id": "M1.D1",
                    "description": "Do you investigate Joe's last known location?",
                    "options": [
                        {
                            "option_id": "M1.D1.O1",
                            "option_name": "Yes, head to the docks.",
                            "consequence": "You discover Joe's boat in disarray, hinting at a struggle.",
                        },
                        {
                            "option_id": "M1.D1.O2",
                            "option_name": "No, talk to the townsfolk first.",
                            "consequence": "You hear rumors of Joe's debts and conflicts with a local gang.",
                        },
                    ],
                },
            ],
        },
        {
            "milestone_id": "M2",
            "description": "A secret underground meeting is discovered.",
            "decision_points": [
                {
                    "decision_point_id": "M2.D1",
                    "description": "Do you attend the meeting undercover?",
                    "options": [
                        {
                            "option_id": "M2.D1.O1",
                            "option_name": "Yes, gather intel.",
                            "consequence": "You overhear plans that could implicate the townsfolk.",
                        },
                        {
                            "option_id": "M2.D1.O2",
                            "option_name": "No, inform the sheriff.",
                            "consequence": "The sheriff's intervention leads to a major arrest but also suspicion on you.",
                        },
                    ],
                },
            ],
        },
    ],
    "endings": [
        {
            "ending_id": "E1",
            "description": "The truth is revealed, leading to justice for Joe, but the town is left divided and fearful.",
        },
        {
            "ending_id": "E2",
            "description": "The mastermind escapes, leaving the town in turmoil and the protagonist with a target on their back.",
        },
        {
            "ending_id": "E3",
            "description": "The protagonist leaves town, haunted by the unresolved mystery and the lives affected by their choices.",
        },
    ],
}
