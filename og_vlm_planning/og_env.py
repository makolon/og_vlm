from typing import List, Optional
import cv2
import base64
import omnigibson as og
from omnigibson.macros import gm
from omnigibson.learning.metrics.task_metric import TaskMetric

gm.ENABLE_OBJECT_STATES = True
gm.USE_GPU_DYNAMICS = True


def get_compatible_scene_model(activity_name, default_scene="house_single_floor"):
    """
    Get appropriate scene model for activity (first preferred).
    """
    activity_scene_mapping = {
        "laying_wood_floors": ["house_single_floor", "house_double_floor_lower"],
        "putting_up_Christmas_decorations_inside": ["house_single_floor"],
        "turning_on_radio": ["house_double_floor_lower"],
        "hiding_Easter_eggs": ["house_double_floor_lower"],
        "rearranging_kitchen_furniture": ["house_double_floor_lower"],
        "picking_up_toys": ["house_single_floor"],
        "setting_mousetraps": ["house_double_floor_upper"],
        "install_air_freshener": ["house_single_floor", "Rs_int"],
        "mopping_floors": ["house_single_floor", "house_double_floor_lower"],
        "making_tea": ["house_single_floor", "house_double_floor_lower"],
        "loading_the_dishwasher": ["house_single_floor", "house_double_floor_lower"],
        "putting_food_in_fridge": ["house_single_floor", "Rs_int"],
        "cooking": ["house_single_floor", "Rs_int"],
        "cleaning": ["house_single_floor", "Rs_int"],
        "organizing": ["house_single_floor", "Rs_int"],
    }
    
    if activity_name in activity_scene_mapping:
        return activity_scene_mapping[activity_name][0]
    else:
        return default_scene


def get_candidate_scene_models(activity_name) -> List[str]:
    """
    Return a prioritized list of candidate scene models for a given activity.
    Falls back to common houses then Rs_int.
    """
    base = {
        "laying_wood_floors": ["house_single_floor", "house_double_floor_lower", "Rs_int"],
        "putting_up_Christmas_decorations_inside": ["house_single_floor", "house_double_floor_lower", "Rs_int"],
        "turning_on_radio": ["house_double_floor_lower", "house_single_floor", "Rs_int"],
        "hiding_Easter_eggs": ["house_double_floor_lower", "house_single_floor", "Rs_int"],
        "rearranging_kitchen_furniture": ["house_double_floor_lower", "house_single_floor", "Rs_int"],
        "picking_up_toys": ["house_single_floor", "house_double_floor_lower", "Rs_int"],
        "setting_mousetraps": ["house_double_floor_upper", "house_double_floor_lower", "house_single_floor", "Rs_int"],
        "install_air_freshener": ["house_single_floor", "Rs_int", "house_double_floor_lower"],
        "mopping_floors": ["house_single_floor", "house_double_floor_lower", "Rs_int"],
        "making_tea": ["house_single_floor", "house_double_floor_lower", "Rs_int"],
        "loading_the_dishwasher": ["house_single_floor", "house_double_floor_lower", "Rs_int"],
        "putting_food_in_fridge": ["house_single_floor", "Rs_int", "house_double_floor_lower"],
        "cooking": ["house_single_floor", "Rs_int", "house_double_floor_lower"],
        "cleaning": ["house_single_floor", "Rs_int", "house_double_floor_lower"],
        "organizing": ["house_single_floor", "Rs_int", "house_double_floor_lower"],
    }
    if activity_name in base:
        return base[activity_name]

    return ["house_single_floor", "house_double_floor_lower", "Rs_int"]


def make_env(activity: str, robot: str = "r1pro", headless: bool = True):
    """
    Create an OmniGibson environment and load a BEHAVIOR activity.
    Config follows upstream BehaviorTask signature.
    """
    robot_type = robot.replace("r1pro", "R1Pro")
    for scene_model in get_candidate_scene_models(activity):
        config = {
            "scene": {
                "type": "InteractiveTraversableScene",
                "scene_model": scene_model,
            },
            "robots": [
                {
                    "type": robot_type,
                    "obs_modalities": ["rgb", "depth"],
                    "action_type": "continuous",
                    "action_normalize": True,
                }
            ],
            "task": {
                "type": "BehaviorTask",
                "activity_name": activity,
                "activity_definition_id": 0,
                "activity_instance_id": 0,
                "online_object_sampling": True,
                "use_presampled_robot_pose": False,
            },
        }
        env = og.Environment(configs=config)
        env.reset()
        return env


def list_scene_names(env, max_items: int = 64) -> List[str]:
    names = []
    for obj in env.scene.objects:
        if hasattr(obj, "name"):
            names.append(obj.name)
    names = list(dict.fromkeys(names))
    return names[:max_items]


def try_rgb_image_b64(env) -> Optional[str]:
    """
    (Optional) Get an RGB image from the environment and return as a base64 string.
    Returns None if not available.
    """
    robot = env.robots[0]
    if hasattr(robot, "get_camera_images"):
        rgb = robot.get_camera_images()["rgb"]
    else:
        return None

    _, buf = cv2.imencode(".png", rgb[..., ::-1])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def bddl_success_fraction(env) -> float:
    """
    Returns the fraction of satisfied BDDL predicates (partial score).
    Depends on OmniGibson's Metric / TerminationCondition; if not available, returns 0/1 approximation.
    """
    # Use TaskMetric if available
    metric = TaskMetric(env=env)
    frac = metric.compute()["predicate_success_fraction"]
    return float(frac)
