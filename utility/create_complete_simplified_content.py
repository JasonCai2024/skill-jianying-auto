#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
????????????simplified_content
"""

import json
import copy
from dataclasses import dataclass
from .complete_materials_builder import CompleteMaterialsBuilder
from .complete_structure_builder import CompleteStructureBuilder
from .complete_tracks_builder_fixed import CompleteTracksBuilderFixed
from typing import Dict, Any

@dataclass(frozen=True)
class CanvasConfigTemplate:
    height: int = 1080
    ratio: str = "16:9"
    width: int = 1920

    def to_dict(self) -> Dict[str, Any]:
        return {"height": self.height, "ratio": self.ratio, "width": self.width}


@dataclass(frozen=True)
class TopLevelTemplate:
    color_space: int = 0
    cover: Any = None
    create_time: int = 0
    extra_info: Any = None
    fps: float = 30.0
    free_render_index_mode_on: bool = False
    group_container: Any = None
    keyframe_graph_list: Any = None
    name: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "color_space": self.color_space,
            "cover": self.cover,
            "create_time": self.create_time,
            "extra_info": self.extra_info,
            "fps": self.fps,
            "free_render_index_mode_on": self.free_render_index_mode_on,
            "group_container": self.group_container,
            "keyframe_graph_list": [] if self.keyframe_graph_list is None else self.keyframe_graph_list,
            "name": self.name,
        }

def _build_segment_material_ref_maps(input_audios, input_videos, speeds, sound_channel_mappings,
                                     vocal_separations, beats, canvases, canvas_id):
    audio_refs = []
    video_refs = []

    segments = [("audio", idx, audio) for idx, audio in enumerate(input_audios)]
    segments.extend([("video", idx, video) for idx, video in enumerate(input_videos)])

    for seg_index, (seg_type, local_index, item) in enumerate(segments):
        speeds_id = speeds[seg_index].get("id", "") if seg_index < len(speeds) else ""
        sound_id = sound_channel_mappings[seg_index].get("id", "") if seg_index < len(sound_channel_mappings) else ""
        vocal_id = vocal_separations[seg_index].get("id", "") if seg_index < len(vocal_separations) else ""

        if seg_type == "audio":
            audio_refs.append({
                "material_id": item.get("id", ""),
                "speeds_id": speeds_id,
                "sound_channel_mappings_id": sound_id,
                "vocal_separations_id": vocal_id,
                "beats_id": beats[local_index].get("id", "") if local_index < len(beats) else ""
            })
        else:
            canvas_ref = canvases[local_index].get("id", "") if local_index < len(canvases) else (canvas_id or "")
            video_refs.append({
                "material_id": item.get("id", ""),
                "speeds_id": speeds_id,
                "sound_channel_mappings_id": sound_id,
                "vocal_separations_id": vocal_id,
                "canvases_id": canvas_ref
            })

    return audio_refs, video_refs

def _build_materials_updates(materials_builder, draft_para_collect):
    return {
        "audios": materials_builder._create_audios(draft_para_collect),
        "videos": materials_builder._create_videos(draft_para_collect),
        "texts": materials_builder._create_texts(draft_para_collect),
        "material_animations": materials_builder._create_material_animations(draft_para_collect),
        "beats": materials_builder._create_beats(draft_para_collect),
        "speeds": materials_builder._create_speeds(draft_para_collect),
        "sound_channel_mappings": materials_builder._create_sound_channel_mappings(draft_para_collect),
        "vocal_separations": materials_builder._create_vocal_separations(draft_para_collect),
        "canvases": materials_builder._create_canvases(draft_para_collect)
    }

def _build_tracks(draft_para_collect):
    tracks_builder = CompleteTracksBuilderFixed()
    return tracks_builder.create_complete_tracks(draft_para_collect)

def _apply_audio_material_refs(draft_para_collect, ref_map):
    input_audios = draft_para_collect.get("audios", []) or []
    for i, audio in enumerate(input_audios):
        if i < len(ref_map):
            audio["speeds_id"] = ref_map[i].get("speeds_id", "")
            audio["sound_channel_mappings_id"] = ref_map[i].get("sound_channel_mappings_id", "")
            audio["vocal_separations_id"] = ref_map[i].get("vocal_separations_id", "")
            audio["beats_id"] = ref_map[i].get("beats_id", "")

def _apply_video_material_refs(draft_para_collect, ref_map):
    input_videos = draft_para_collect.get("videos", []) or []
    for j, video in enumerate(input_videos):
        if j < len(ref_map):
            video["speeds_id"] = ref_map[j].get("speeds_id", "")
            video["sound_channel_mappings_id"] = ref_map[j].get("sound_channel_mappings_id", "")
            video["vocal_separations_id"] = ref_map[j].get("vocal_separations_id", "")
            if not video.get("canvases_id"):
                video["canvases_id"] = ref_map[j].get("canvases_id", "")

def _build_segment_materials(materials_builder, draft_para_collect, canvas_id, existing_lists):
    input_audios = draft_para_collect.get("audios", []) or []
    input_videos = draft_para_collect.get("videos", []) or []
    total_segments = len(input_audios) + len(input_videos)

    template = getattr(materials_builder, "source_template", {}) or {}
    speeds_t = template.get("speeds", []) or []
    sound_t = template.get("sound_channel_mappings", []) or []
    vocal_t = template.get("vocal_separations", []) or []
    beats_t = template.get("beats", []) or []
    canvases_t = template.get("canvases", []) or []

    speeds = []
    sound_channel_mappings = []
    vocal_separations = []
    beats = []
    canvases = []

    if speeds_t and sound_t and vocal_t:
        for i in range(total_segments):
            speed = speeds_t[i % len(speeds_t)].copy()
            speed["id"] = materials_builder.generate_beat_id()
            speeds.append(speed)

            mapping = sound_t[i % len(sound_t)].copy()
            mapping["id"] = materials_builder.generate_beat_id()
            sound_channel_mappings.append(mapping)

            vocal = vocal_t[i % len(vocal_t)].copy()
            vocal["id"] = materials_builder.generate_beat_id()
            vocal_separations.append(vocal)
    else:
        speeds = existing_lists.get("speeds", [])
        sound_channel_mappings = existing_lists.get("sound_channel_mappings", [])
        vocal_separations = existing_lists.get("vocal_separations", [])

    beats = existing_lists.get("beats", [])

    if canvases_t:
        for j in range(len(input_videos)):
            canvas = canvases_t[j % len(canvases_t)].copy()
            vid = input_videos[j]
            cid = vid.get("canvases_id") or canvas_id or ""
            if cid:
                canvas["id"] = cid
            canvases.append(canvas)
    else:
        canvases = existing_lists.get("canvases", [])

    return {
        "speeds": speeds,
        "sound_channel_mappings": sound_channel_mappings,
        "vocal_separations": vocal_separations,
        "beats": beats,
        "canvases": canvases
    }

def _build_top_level_content(canvas, duration_microseconds, complete_config, complete_keyframes,
                             complete_platform, complete_last_modified_platform, complete_materials,
                             complete_tracks, missing_fields, canvas_id):
    canvas_template = CanvasConfigTemplate()
    canvas_config = canvas_template.to_dict()
    canvas_config["height"] = canvas.get("height", canvas_template.height)
    canvas_config["width"] = canvas.get("width", canvas_template.width)

    top_template = TopLevelTemplate()
    content = top_template.to_dict()
    content.update({
        "canvas_config": canvas_config,
        "config": complete_config,
        "duration": duration_microseconds,
        "id": canvas_id,
        "keyframes": complete_keyframes,
        "last_modified_platform": complete_last_modified_platform,
        "materials": complete_materials,
        "mutable_config": missing_fields.get("mutable_config"),
        "new_version": missing_fields.get("new_version"),
        "platform": complete_platform,
        "relationships": missing_fields.get("relationships"),
        "render_index_track_mode_on": missing_fields.get("render_index_track_mode_on"),
        "retouch_cover": missing_fields.get("retouch_cover"),
        "source": missing_fields.get("source"),
        "static_cover_image_path": missing_fields.get("static_cover_image_path"),
        "time_marks": missing_fields.get("time_marks"),
        "tracks": complete_tracks,
        "update_time": missing_fields.get("update_time"),
        "version": missing_fields.get("version")
    })
    return content

def create_complete_simplified_content(
    draft_para_collect: Dict[str, Any],
    template_content: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    ????????????simplified_content
    
    Args:
        draft_para_collect (Dict[str, Any]): ???????
        
    Returns:
        Dict[str, Any]: ??????????????
    """
    try:
        canvas = draft_para_collect.get("canvas", {})
        canvas_id = canvas.get("id", "")
        canvas_duration = canvas.get("duration", 0)
        
        # ?????
        duration_microseconds = int(canvas_duration * 1000000)
        
        print("?? ????????????simplified_content...")
        
        # 1) ??????? (materials)
        materials_builder = CompleteMaterialsBuilder()
        use_template = bool(template_content)
        base_content = copy.deepcopy(template_content) if template_content else {}
        base_materials = copy.deepcopy(base_content.get("materials", {})) if base_content else {}
        # ??????????????????
        if base_materials is None:
            base_materials = {}

        materials_updates = _build_materials_updates(materials_builder, draft_para_collect)

        # 2) ??????ID???audio/video -> speeds/sound_channel_mappings/vocal_separations/beats?
        existing_lists = {
            "speeds": materials_updates.get("speeds", []) or [],
            "sound_channel_mappings": materials_updates.get("sound_channel_mappings", []) or [],
            "vocal_separations": materials_updates.get("vocal_separations", []) or [],
            "beats": materials_updates.get("beats", []) or [],
            "canvases": materials_updates.get("canvases", []) or []
        }
        segment_materials = _build_segment_materials(materials_builder, draft_para_collect, canvas_id, existing_lists)
        materials_updates["speeds"] = segment_materials["speeds"]
        materials_updates["sound_channel_mappings"] = segment_materials["sound_channel_mappings"]
        materials_updates["vocal_separations"] = segment_materials["vocal_separations"]
        materials_updates["beats"] = segment_materials["beats"]
        materials_updates["canvases"] = segment_materials["canvases"]

        speeds = materials_updates.get("speeds", []) or []
        sound_channel_mappings = materials_updates.get("sound_channel_mappings", []) or []
        vocal_separations = materials_updates.get("vocal_separations", []) or []
        beats = materials_updates.get("beats", []) or []
        canvases = materials_updates.get("canvases", []) or []
        canvas_id = canvas.get("id", "")
        input_audios = draft_para_collect.get("audios", []) or []
        input_videos = draft_para_collect.get("videos", []) or []
        audio_ref_map, video_ref_map = _build_segment_material_ref_maps(
            input_audios,
            input_videos,
            speeds,
            sound_channel_mappings,
            vocal_separations,
            beats,
            canvases,
            canvas_id
        )
        _apply_audio_material_refs(draft_para_collect, audio_ref_map)
        _apply_video_material_refs(draft_para_collect, video_ref_map)
        
        # 3) ??????tracks?? keyframes
        structure_builder = CompleteStructureBuilder()
        complete_keyframes = structure_builder.create_complete_keyframes(draft_para_collect)
        # ????keyframes??texts????????????
        complete_keyframes["texts"] = []
        # videos???CompleteMaterialsBuilder?????????
        # complete_keyframes["videos"] = []
        complete_tracks = _build_tracks(draft_para_collect)

        if use_template:
            simplified_content = base_content
            if "canvas_config" not in simplified_content:
                simplified_content["canvas_config"] = CanvasConfigTemplate().to_dict()
            simplified_content["keyframes"] = complete_keyframes
            simplified_content["tracks"] = complete_tracks

            base_materials.update(materials_updates)
            simplified_content["materials"] = base_materials
        else:
            complete_config = structure_builder.create_complete_config(draft_para_collect)
            complete_platform = structure_builder.create_complete_platform(draft_para_collect)
            complete_last_modified_platform = structure_builder.create_complete_last_modified_platform(draft_para_collect)
            missing_fields = structure_builder.create_missing_top_level_fields(draft_para_collect)
            # ??????? - ????????28?????
            complete_materials = materials_builder.create_complete_materials(draft_para_collect)
            complete_materials.update(materials_updates)
            simplified_content = _build_top_level_content(
                canvas,
                duration_microseconds,
                complete_config,
                complete_keyframes,
                complete_platform,
                complete_last_modified_platform,
                complete_materials,
                complete_tracks,
                missing_fields,
                canvas_id
            )
        
        print(f"? simplified_content???????{len(simplified_content)}?????")
        print(f"   materials??{len(simplified_content.get('materials', {}))}???")
        
        # ??????
        validation_result = validate_simplified_content(simplified_content)
        print(f"?? ????: {validation_result['valid']}")
        if not validation_result['valid']:
            print(f"   ??: {validation_result['issues']}")
        
        return simplified_content
        
    except Exception as e:
        print(f"? ??simplified_content??: {e}")
        import traceback
        traceback.print_exc()
        return {}

def validate_simplified_content(content: Dict[str, Any]) -> Dict[str, Any]:
    """??simplified_content???"""
    issues = []
    
    # ??????
    required_fields = [
        "canvas_config", "color_space", "config", "cover", "create_time",
        "duration", "extra_info", "fps", "free_render_index_mode_on",
        "group_container", "id", "keyframe_graph_list", "keyframes",
        "last_modified_platform", "materials", "mutable_config", "name",
        "new_version", "platform", "relationships", "render_index_track_mode_on",
        "retouch_cover", "source", "static_cover_image_path", "time_marks",
        "tracks", "update_time", "version"
    ]
    
    missing_fields = []
    for field in required_fields:
        if field not in content:
            missing_fields.append(field)
    
    if missing_fields:
        issues.append(f"??????: {missing_fields}")
    
    # ??materials??
    materials = content.get("materials", {})
    required_material_fields = [
        "ai_translates", "audio_balances", "audio_effects", "audio_fades",
        "audio_track_indexes", "audios", "beats", "canvases", "chromas",
        "color_curves", "digital_humans", "drafts", "effects",
        "flowers", "green_screens", "handwrites", "hsl", "images",
        "log_color_wheels", "loudnesses", "manual_deformations", "masks",
        "material_animations", "material_colors", "multi_language_refs",
        "placeholders", "plugin_effects", "primary_color_wheels",
        "realtime_denoises", "shapes", "smart_crops", "smart_relights",
        "sound_channel_mappings", "speeds", "stickers", "tail_leaders",
        "text_templates", "texts", "time_marks", "transitions",
        "video_effects", "video_trackings", "videos", "vocal_beautifys",
        "vocal_separations"
    ]
    
    missing_material_fields = []
    for field in required_material_fields:
        if field not in materials:
            missing_material_fields.append(field)
    
    if missing_material_fields:
        issues.append(f"??materials??: {missing_material_fields}")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "total_top_fields": len(content),
        "expected_top_fields": len(required_fields),
        "total_material_fields": len(materials),
        "expected_material_fields": len(required_material_fields)
    }

def main():
    """?????simplified_content??"""
    print("?? ????simplified_content??...")
    
    test_draft_para = {
        "canvas": {
            "id": "F2FD0F1C-6737-42ed-9A70-E66E37358546",
            "duration": 12,
            "width": 1920,
            "height": 1080
        }
    }
    
    complete_content = create_complete_simplified_content(test_draft_para)
    
    if complete_content:
        # ????
        with open("complete_simplified_content_test.json", 'w', encoding='utf-8') as f:
            json.dump(complete_content, f, ensure_ascii=False, indent=2)
        
        print("? ??simplified_content???? complete_simplified_content_test.json")
        return True
    else:
        print("? ????")
        return False

if __name__ == "__main__":
    main()
