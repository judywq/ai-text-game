# ruff: noqa: E501, PERF401
import logging
from typing import TypedDict

from langchain_core.output_parsers.json import JsonOutputParser
from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END
from langgraph.graph import START
from langgraph.graph import StateGraph

logger = logging.getLogger(__name__)


# Type definitions
class DecisionOption(TypedDict):
    option_id: str
    option_name: str
    consequence: str


class DecisionPoint(TypedDict):
    decision_point_id: str
    description: str
    options: list[DecisionOption]


class Milestone(TypedDict):
    milestone_id: str
    description: str
    decision_points: list[DecisionPoint]


class Ending(TypedDict):
    ending_id: str
    description: str


class StorySkeleton(TypedDict):
    story_background: str
    milestones: list[Milestone]
    endings: list[Ending]


class StoryState(TypedDict):
    story_skeleton: StorySkeleton
    current_decision_point: str
    story_progress: list[str]
    chosen_decisions: list[str]
    cefr_level: str
    story_text: str
    status: str


class StoryGraph:
    """Encapsulates story generation graph functionality."""

    def __init__(self, llm_models: dict[str, Runnable]):
        """Initialize with LLM models for each node type.

        Args:
            llm_models: Dictionary mapping node types to LLM models
        """
        self.llm_models = llm_models
        self.graph = self._build_graph()
        self.json_parser = JsonOutputParser()

    def _build_graph(self) -> StateGraph:
        """Build the story generation graph."""
        workflow = StateGraph(state_schema=StoryState)

        # Add nodes
        workflow.add_node("generate_story_delta", self.generate_story_delta)
        workflow.add_node("generate_story_ending", self.generate_story_ending)

        # Add edges
        workflow.add_conditional_edges(
            START,
            self.decide_continue_or_end,
            {
                "generate_story_delta": "generate_story_delta",
                "generate_story_ending": "generate_story_ending",
            },
        )
        workflow.add_edge(
            ["generate_story_delta", "generate_story_ending"],
            END,
        )

        return workflow.compile(checkpointer=InMemorySaver())

    def generate_story_delta(self, state: StoryState) -> StoryState:
        """Generate the next story segment."""
        logger.info(
            "Generating story delta for %s",
            state.get("current_decision_point", ""),
        )
        try:
            # Get current milestone info
            skeleton = state["story_skeleton"]
            milestone_id, decision_point_id = get_m_d_id(
                state["current_decision_point"],
            )
            milestone = next(
                m for m in skeleton["milestones"] if m["milestone_id"] == milestone_id
            )
            decision_point = next(
                d
                for d in milestone["decision_points"]
                if d["decision_point_id"] == decision_point_id
            )
            formatted_progress = format_progress_with_decisions(state)
            if not formatted_progress:
                formatted_progress = "(There is no progress yet: please start writing the story from the background)"
            formatted_skeleton = format_story_skeleton(skeleton)
            formatted_milestone = format_milestone(milestone)
            formatted_decision_point = format_decision_point(decision_point)

            params = {
                "skeleton": formatted_skeleton,
                "background": skeleton["story_background"],
                "progress": formatted_progress,
                "milestone": formatted_milestone,
                "decisions_made": format_decisions_made(state),
                "cefr_level": state["cefr_level"],
                "decision_point": formatted_decision_point,
            }

            # Generate continuation
            chain = self.llm_models["continuation"]
            story_segment = chain.invoke(params).content

        except Exception:
            logger.exception("Error generating story delta")
            raise
        else:
            return {
                "story_text": story_segment,
                "status": "IN_PROGRESS",
            }

    def generate_story_ending(self, state: StoryState) -> StoryState:
        """Generate the story ending."""
        logger.info(
            "Generating story ending for %s",
            state.get("current_decision_point", ""),
        )

        try:
            # Format variables
            variables = {
                "decisions_made": format_decisions_made(state),
                "skeleton": format_story_skeleton(state["story_skeleton"]),
                "progress": format_progress_with_decisions(state),
                "cefr_level": state["cefr_level"],
            }

            # Generate ending
            chain = self.llm_models["ending"]
            ending = chain.invoke(variables).content

        except Exception:
            logger.exception("Error generating story ending")
            raise
        else:
            return {
                "story_text": ending,
                "status": "COMPLETED",
            }

    @staticmethod
    def decide_continue_or_end(state: StoryState) -> str:
        """Decide whether to continue the story or generate an ending."""
        if state.get("current_decision_point", "") == "":
            return "generate_story_ending"
        return "generate_story_delta"

    def invoke(self, state: StoryState, config: dict | None = None) -> StoryState:
        """Run the story graph with the given state."""
        return self.graph.invoke(state, config)


# Helper functions
def get_m_d_id(decision_point_id: str) -> tuple[str, str]:
    """Get milestone, and decision IDs from a decision point ID."""
    m, d = decision_point_id.split(".")
    return f"{m}", f"{m}.{d}"


def get_decision_point(
    skeleton: StorySkeleton,
    decision_point_id: str,
) -> DecisionPoint:
    """Get a decision point from the story skeleton."""
    for milestone in skeleton["milestones"]:
        for decision_point in milestone["decision_points"]:
            if decision_point["decision_point_id"] == decision_point_id:
                return decision_point
    msg = f"Decision point {decision_point_id} not found"
    raise ValueError(msg)


def get_decision_option(skeleton: StorySkeleton, option_id: str) -> DecisionOption:
    """Get a decision option from the story skeleton."""
    for milestone in skeleton["milestones"]:
        for decision_point in milestone["decision_points"]:
            for option in decision_point["options"]:
                if option["option_id"] == option_id:
                    return option
    msg = f"Decision option {option_id} not found"
    raise ValueError(msg)


def format_decision_option(decision_option: DecisionOption) -> str:
    return (
        f"[{decision_option['option_id']}] {decision_option['option_name']}\n"
        f"consequence: {decision_option['consequence']}"
    )


def format_progress_with_decisions(state: dict) -> str:
    """Format story progress with decisions for prompt context."""
    story_progress = state["story_progress"]
    if len(story_progress) <= 0:
        return ""

    decisions = state["chosen_decisions"]
    formatted_progress = ""
    for i, progress in enumerate(story_progress):
        formatted_progress += f"{progress}\n"

        if i < len(decisions):
            decision = decisions[i]
            decision_option = get_decision_option(state["story_skeleton"], decision)
            formatted_progress += f"\n[Choice made: {decision_option['option_name']}]\n"
    return formatted_progress


def format_decisions_made(state: dict) -> str:
    """Format decisions made for prompt context."""
    choices = state.get("chosen_decisions", [])
    decisions_made = "(NONE YET)"
    if len(choices) > 0:
        last_choice_id = choices[-1]
        last_choice = get_decision_option(state["story_skeleton"], last_choice_id)
        decisions_made = format_decision_option(last_choice)

    return decisions_made


def format_milestone(milestone: Milestone) -> str:
    return f"Milestone [{milestone['milestone_id']}]: {milestone['description']}\n"


def format_decision_point(decision_point: DecisionPoint) -> str:
    return (
        f"DecisionPoint [{decision_point['decision_point_id']}]: "
        f"{decision_point['description']}\n"
        f"Options:\n"
        + "\n".join(
            [f"    - {option['option_name']}" for option in decision_point["options"]],
        )
    )


def format_story_skeleton(skeleton: StorySkeleton) -> str:
    formatted_parts = []
    # Format story background
    formatted_parts.append(f"### Story Background: {skeleton['story_background']}\n")

    if endings := skeleton.get("endings", []):
        # Format endings
        formatted_parts.append("\n### Possible Endings:")
        formatted_parts.extend(
            [
                f"- Ending [{ending['ending_id']}]: {ending['description']}"
                for ending in endings
            ],
        )

    if milestones := skeleton.get("milestones", []):
        # Format milestones
        formatted_parts.append("### Milestones")
        for milestone in milestones:
            if not milestone:
                # An empty milestone, might be the in-progress skeleton
                continue
            formatted_parts.append(
                f"- Milestone [{milestone['milestone_id']}]: {milestone['description']}",
            )
            # Format decision points
            for decision in milestone["decision_points"]:
                formatted_parts.append(
                    (
                        f"  - DecisionPoint [{decision['decision_point_id']}]:"
                        f" {decision['description']}"
                    ),
                )
                # Format options
                for option in decision["options"]:
                    formatted_parts.append(
                        f"    - {option['option_name']}",
                    )
    else:
        logger.error("No milestones found in skeleton")

    return "\n".join(formatted_parts)
