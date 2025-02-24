# ruff: noqa: E501

import json

from langchain_community.chat_models.fake import FakeListChatModel


def get_fake_llm_model(node_name):
    if node_name == "skeleton":
        return FakeListChatModel(responses=[json.dumps(skeleton_json)])
    if node_name == "continuation":
        return FakeListChatModel(responses=["This is a continuation of the story."])
    if node_name == "ending":
        return FakeListChatModel(responses=["This is the ending of the story."])
    if node_name == "cefr":
        return FakeListChatModel(
            responses=[
                json.dumps(
                    {
                        "story_text": "This is the CEFR-adjusted story text.",
                        "decision_point": {
                            "decision_point_id": "C1.M1.D1",
                            "description": "What do you do next?",
                            "options": [
                                {
                                    "option_id": "C1.M1.D1.O1",
                                    "option_name": "Option 1",
                                    "consequence": "Consequence 1",
                                },
                                {
                                    "option_id": "C1.M1.D1.O2",
                                    "option_name": "Option 2",
                                    "consequence": "Consequence 2",
                                },
                            ],
                        },
                    },
                ),
            ],
        )
    return None


skeleton_json = {
    "story_background": "A mysterious series of events unfolds in the small coastal town of Seabreeze, where a once-peaceful community becomes embroiled in secrets, betrayal, and the quest for truth after a local fisherman disappears under suspicious circumstances.",
    "chapters": [
        {
            "chapter_id": "C1",
            "milestones": [
                {
                    "milestone_id": "C1.M1",
                    "description": "The disappearance of Joe, a local fisherman, is reported to the town sheriff.",
                    "decision_points": [
                        {
                            "decision_point_id": "C1.M1.D1",
                            "description": "Do you investigate Joe's last known location?",
                            "options": [
                                {
                                    "option_id": "C1.M1.D1.O1",
                                    "option_name": "Yes, head to the docks.",
                                    "consequence": "You discover Joe's boat in disarray, hinting at a struggle.",
                                },
                                {
                                    "option_id": "C1.M1.D1.O2",
                                    "option_name": "No, talk to the townsfolk first.",
                                    "consequence": "You hear rumors of Joe's debts and conflicts with a local gang.",
                                },
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "chapter_id": "C2",
            "milestones": [
                {
                    "milestone_id": "C2.M1",
                    "description": "A secret underground meeting is discovered.",
                    "decision_points": [
                        {
                            "decision_point_id": "C2.M1.D1",
                            "description": "Do you attend the meeting undercover?",
                            "options": [
                                {
                                    "option_id": "C2.M1.D1.O1",
                                    "option_name": "Yes, gather intel.",
                                    "consequence": "You overhear plans that could implicate the townsfolk.",
                                },
                                {
                                    "option_id": "C2.M1.D1.O2",
                                    "option_name": "No, inform the sheriff.",
                                    "consequence": "The sheriff's intervention leads to a major arrest but also suspicion on you.",
                                },
                            ],
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
