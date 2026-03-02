from langgraph.graph import StateGraph, END

from app.graph.state import StoryState
from app.graph.nodes.story_writer import story_writer
from app.graph.nodes.script_splitter import script_splitter
from app.graph.nodes.voice_synthesizer import voice_synthesizer
from app.graph.nodes.audio_stitcher import audio_stitcher


def create_story_pipeline():
    graph = StateGraph(StoryState)

    graph.add_node("story_writer", story_writer)
    graph.add_node("script_splitter", script_splitter)
    graph.add_node("voice_synthesizer", voice_synthesizer)
    graph.add_node("audio_stitcher", audio_stitcher)

    graph.set_entry_point("story_writer")
    graph.add_edge("story_writer", "script_splitter")
    graph.add_edge("script_splitter", "voice_synthesizer")
    graph.add_edge("voice_synthesizer", "audio_stitcher")
    graph.add_edge("audio_stitcher", END)

    return graph.compile()
